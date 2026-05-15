import requests
import base64
import tempfile
import os
import yaml
import html.parser
import urllib.parse
import re
from typing import List, Dict, Optional, Tuple


class MFARequired(Exception):
    """Výjimka signalizující, že PingFederate vyžaduje MFA OTP kód k dokončení přihlášení."""
    def __init__(self, state: dict):
        super().__init__("MFA ověření vyžadováno — zadejte OTP kód z autentifikátoru")
        self.state = state


class PushPending(Exception):
    """PingFederate čeká na schválení PingID push notifikace na mobilu.
    Uživatel musí schválit push v PingID aplikaci, poté kliknout tlačítko v UI.
    """
    def __init__(self, state: dict):
        super().__init__("PingID push notifikace odeslána — schvalte ji na mobilu")
        self.state = state


class _FormParser(html.parser.HTMLParser):
    """Jednoduchý parser HTML formulářů pro SAML login simulaci."""
    def __init__(self):
        super().__init__()
        self.forms: List[Dict] = []
        self._form: Optional[Dict] = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'form':
            method = a.get('method', 'get').lower()
            if method == 'post':
                self._form = {
                    'action': a.get('action', ''),
                    'inputs': {},
                    'text_inputs': [],
                    'password_inputs': [],
                }
                self.forms.append(self._form)
        elif tag == 'input' and self._form is not None:
            t = a.get('type', 'text').lower()
            name = a.get('name', '')
            value = a.get('value', '')
            if not name:
                return
            if t == 'hidden':
                self._form['inputs'][name] = value
            elif t == 'radio':
                # Take first value for each radio group; override with checked one
                is_checked = 'checked' in a or a.get('checked') is not None
                if name not in self._form['inputs'] or is_checked:
                    self._form['inputs'][name] = value
                # Track radio group for push-preference selection
                rg = self._form.setdefault('_radio_groups', {})
                rg.setdefault(name, []).append({'value': value, 'checked': is_checked})
            elif t in ('text', 'email'):
                self._form['text_inputs'].append(name)
                self._form['inputs'][name] = value
            elif t == 'password':
                self._form['password_inputs'].append(name)
                self._form['inputs'][name] = value

    def handle_endtag(self, tag):
        if tag == 'form':
            self._form = None


def _detect_mfa_form(html_text: str, forms: List[Dict]) -> Optional[Dict]:
    """Detekuje MFA challenge formulář PingID/PingFederate.
    Vrátí form dict s extra klíčem 'otp_field', nebo None pokud není MFA stránka.
    """
    OTP_FIELD_NAMES = {'otp', 'passcode', 'pf.otp', 'code', 'token',
                       'mfa_token', 'one_time_password', 'otpcode', 'authcode'}
    MFA_INDICATORS = ['pingid', 'one-time', 'verification code', 'authenticator',
                      'passcode', 'enter your code', 'second factor', 'authentication code']
    html_lower = html_text.lower()
    is_mfa_page = any(ind in html_lower for ind in MFA_INDICATORS)

    for form in forms:
        if 'SAMLResponse' in form['inputs']:
            continue
        all_fields = form['text_inputs'] + form['password_inputs']
        otp_field = next((f for f in all_fields if f.lower() in OTP_FIELD_NAMES), None)
        if not otp_field and is_mfa_page:
            non_login = [f for f in all_fields
                         if f.lower() not in {'pf.username', 'username', 'pf.pass',
                                              'password', 'email', 'user', 'login'}]
            otp_field = non_login[0] if non_login else None
        if otp_field:
            return {**form, 'otp_field': otp_field}
    return None


class RancherClient:
    """Client pro připojení k Rancher API a správu Kubernetes clusterů"""

    def __init__(self, rancher_url: str, access_key: str = '', secret_key: str = '', verify_ssl: bool = True, ca_cert: Optional[str] = None, bearer_token: Optional[str] = None):
        """
        Inicializace Rancher klienta

        Args:
            rancher_url: URL Rancher serveru (např. https://rancher.example.com)
            access_key: Rancher API access key (nebo prázdný při použití bearer_token)
            secret_key: Rancher API secret key (nebo prázdný při použití bearer_token)
            verify_ssl: Ověřovat SSL certifikáty
            ca_cert: Cesta k CA certifikátu (volitelné, default: FaureciaRootCA.cer)
            bearer_token: Bearer token (z username/password login) – nahrazuje access_key/secret_key
        """
        self.rancher_url = rancher_url.rstrip('/')
        self.access_key = access_key
        self.secret_key = secret_key
        self.bearer_token = bearer_token

        # Nastavení SSL verifikace s podporou CA certifikátu
        if verify_ssl:
            if ca_cert is None:
                # Zkusit ca-bundle.pem (kompletní bundle), pak FaureciaRootCA.cer jako fallback
                base_dir = os.path.dirname(os.path.abspath(__file__))
                for name in ('ca-bundle.pem', 'FaureciaRootCA.cer'):
                    default_ca = os.path.join(base_dir, name)
                    if os.path.exists(default_ca):
                        self.verify_ssl = default_ca
                        print(f"Používám CA bundle: {default_ca}")
                        break
                else:
                    # Fallback na True (použije systémové CA certs)
                    self.verify_ssl = True
            elif os.path.exists(ca_cert):
                self.verify_ssl = ca_cert
                print(f"Používám CA certifikát: {ca_cert}")
            else:
                self.verify_ssl = True
        else:
            self.verify_ssl = False

        self.session = requests.Session()

        if bearer_token:
            # Bearer token z username/password login
            self.session.headers.update({
                'Authorization': f'Bearer {bearer_token}',
                'Content-Type': 'application/json'
            })
        else:
            # Basic Auth s access_key:secret_key
            auth_string = f"{access_key}:{secret_key}"
            encoded = base64.b64encode(auth_string.encode()).decode()
            self.session.headers.update({
                'Authorization': f'Basic {encoded}',
                'Content-Type': 'application/json'
            })

    @classmethod
    def _resolve_verify(cls, verify_ssl: bool, ca_cert: Optional[str]) -> object:
        """Vrátí verify parametr pro requests (True/False/cesta k CA bundlu)."""
        if not verify_ssl:
            return False
        if ca_cert and os.path.exists(ca_cert):
            return ca_cert
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Kompletní bundle všech firemních CA (chain_bundle)
        for name in ('ca-bundle.pem', 'FaureciaRootCA.cer'):
            path = os.path.join(base_dir, name)
            if os.path.exists(path):
                return path
        return True

    @classmethod
    def get_auth_providers(cls, rancher_url: str, verify_ssl: bool = True,
                           ca_cert: Optional[str] = None) -> List[Dict]:
        """
        Vrátí seznam dostupných auth providerů z Rancher /v3-public/authProviders.

        Returns:
            List[Dict] s klíči 'id' a 'type', např.:
            [{'id': 'activedirectory', 'type': 'activeDirectoryProvider'},
             {'id': 'local', 'type': 'localProvider'}]
        """
        verify = cls._resolve_verify(verify_ssl, ca_cert)
        try:
            resp = requests.get(
                f"{rancher_url.rstrip('/')}/v3-public/authProviders",
                verify=verify, timeout=10
            )
            resp.raise_for_status()
            return [{'id': p.get('id'), 'type': p.get('type')}
                    for p in resp.json().get('data', [])]
        except requests.exceptions.SSLError:
            # SSL chyba - vrátíme prázdný list, from_credentials dá hint uživateli
            return [{'id': '__ssl_error__', 'type': ''}]
        except Exception:
            return []

    @classmethod
    def from_credentials(cls, rancher_url: str, username: str, password: str,
                         verify_ssl: bool = True, ca_cert: Optional[str] = None,
                         provider: Optional[str] = None) -> 'RancherClient':
        """
        Přihlášení k Rancher pomocí uživatelského jména a hesla.
        Auto-detekuje auth provider (local → ActiveDirectory).
        Rancher vrátí Bearer token pro další API volání.

        Args:
            rancher_url: URL Rancher serveru
            username: Uživatelské jméno (bez domény, tu dodá defaultLoginDomain)
            password: Heslo
            verify_ssl: Ověřovat SSL certifikáty
            ca_cert: Cesta k CA certifikátu
            provider: Explicitní provider ('local' nebo 'activedirectory'), None = auto

        Returns:
            RancherClient instance s Bearer token autentifikací

        Raises:
            Exception: Při chybě přihlášení s detailní zprávou
        """
        url = rancher_url.rstrip('/')
        verify = cls._resolve_verify(verify_ssl, ca_cert)
        saml_found = []

        # Mapování provider id → endpoint URL
        provider_endpoints = {
            'local': f"{url}/v3-public/localProviders/local?action=login",
            'activedirectory': f"{url}/v3-public/activeDirectoryProviders/activedirectory?action=login",
        }

        # Providery které vyžadují browser redirect (SAML/OAuth) – nelze použít s username/password
        SAML_PROVIDERS = {'ping', 'shibboleth', 'okta', 'adfs', 'keycloak',
                          'googleoauth', 'github', 'azuread', 'saml'}

        # Pořadí providerů k vyzkoušení
        if provider:
            providers_to_try = [provider]
        else:
            # Auto-detekce: zjistit z API, preferovat non-local (AD) před local
            available = cls.get_auth_providers(url, verify_ssl, ca_cert)
            # SSL chyba při načítání providerů
            if any(p['id'] == '__ssl_error__' for p in available):
                raise Exception(
                    "SSL chyba při připojení k Rancher. Vypněte 'Ověřovat SSL certifikáty' a zkuste znovu."
                )
            available_ids = [p['id'] for p in available]

            # Zjistit SAML providery v tomto Rancher instanci
            saml_found = [p for p in available_ids if p in SAML_PROVIDERS]
            # Interaktivní (password-based) providery
            interactive = [p for p in ['activedirectory', 'local'] if p in available_ids]

            providers_to_try = interactive if interactive else ['local']  # fallback

        last_error = None
        for prov in providers_to_try:
            endpoint = provider_endpoints.get(prov)
            if not endpoint:
                continue

            try:
                resp = requests.post(
                    endpoint,
                    json={"username": username, "password": password, "ttl": 57600000},
                    verify=verify,
                    timeout=15
                )

                data = resp.json() if resp.content else {}

                if resp.ok and data.get('type') != 'error':
                    token = data.get('token')
                    if token:
                        return cls(
                            rancher_url=url,
                            verify_ssl=verify_ssl,
                            ca_cert=ca_cert,
                            bearer_token=token
                        )

                # Uložit chybu a zkusit další provider
                msg = data.get('message', resp.text) if data else resp.text
                last_error = f"[{prov}] {resp.status_code}: {msg}"

            except requests.exceptions.SSLError as e:
                last_error = f"[{prov}] SSL chyba (zkuste vypnout 'Ověřovat SSL certifikáty'): {str(e)[:120]}"
            except requests.exceptions.ConnectionError:
                last_error = f"[{prov}] Nelze se připojit k {url}"
            except requests.exceptions.Timeout:
                last_error = f"[{prov}] Timeout při přihlášení"
            except Exception as e:
                last_error = f"[{prov}] {str(e)}"
        # Všechny interaktivní providery selhaly — zkusit SAML browser flow jako fallback
        if saml_found:
            try:
                token = cls._saml_login(url, username, password, verify_ssl, ca_cert)
                return cls(rancher_url=url, verify_ssl=verify_ssl, ca_cert=ca_cert, bearer_token=token)
            except MFARequired:
                raise  # propagovat do app.py — UI zobrazí OTP vstup
            except PushPending:
                raise  # propagovat do app.py — UI zobrazí "Schválil jsem" tlačítko
            except Exception as saml_err:
                raise Exception(
                    f"Přihlášení selhalo: {last_error}\n"
                    f"SAML ({', '.join(saml_found)}) také selhalo: {saml_err}"
                )
        raise Exception(f"Přihlášení selhalo: {last_error}"
                        + (f"\n\U0001f4a1 Tento Rancher používá SSO ({', '.join(saml_found)}) \u2014 zkusím přihlášení přes SAML form..."
                           if saml_found else ""))

    @classmethod
    def get_ping_redirect_url(cls, rancher_url: str, verify_ssl: bool = True,
                              ca_cert: Optional[str] = None) -> str:
        """
        Inicializuje PingID SAML flow a vrátí URL pro přihlášení v prohlížeči.
        Používá se pro browser-based auth (push notifikace, MFA).

        Returns:
            idpRedirectUrl — URL pro otevření v prohlížeči
        Raises:
            Exception: Pokud Rancher nevrátí redirect URL
        """
        url = rancher_url.rstrip('/')
        verify = cls._resolve_verify(verify_ssl, ca_cert)
        try:
            resp = requests.post(
                f"{url}/v3-public/pingProviders/ping?action=login",
                json={"finalRedirectUrl": f"{url}/dashboard/"},
                verify=verify,
                timeout=15,
            )
            resp.raise_for_status()
            idp_url = resp.json().get('idpRedirectUrl')
        except Exception as e:
            raise Exception(f"Nelze získat PingID redirect URL: {e}")
        if not idp_url:
            raise Exception("Rancher nevrátil idpRedirectUrl")
        return idp_url

    @classmethod
    def _saml_login(cls, rancher_url: str, username: str, password: str,
                    verify_ssl: bool = True, ca_cert: Optional[str] = None) -> str:
        """
        Přihlášení přes SAML/PingID provider simulací browser flow.
        1. POST /v3-public/pingProviders/ping?action=login → idpRedirectUrl
        2. GET idpRedirectUrl → PingFederate formulář (pf.username, pf.pass)
        3. POST formulář na PingFederate → SAML ACS callback na Rancher
        4. Rancher ACS /v1-saml/ping/saml/acs → R_SESS cookie = Bearer token

        Returns:
            Bearer token (R_SESS cookie)
        Raises:
            Exception: Při chybě přihlášení
        """
        url = rancher_url.rstrip('/')
        verify = cls._resolve_verify(verify_ssl, ca_cert)

        # Dva oddělené sessions:
        # - rancher_session: BEZ browser User-Agent (jinak Rancher vyžaduje CSRF token → 422)
        # - idp_session: s Mozilla UA (PingFederate vyžaduje browser-like UA)
        #   IdP (aser0001.ww.faurecia.com) je externý server — verify=False (má vlastní CA)
        BROWSER_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

        rancher_session = requests.Session()
        rancher_session.verify = verify

        idp_session = requests.Session()
        idp_session.verify = False  # IdP je externý server s jiným CA než Rancher
        idp_session.headers.update({'User-Agent': BROWSER_UA})

        # Krok 1: Inicializace SAML flow → získat idpRedirectUrl od Rancher
        # Poznámka: bez browser UA, jinak Rancher detekuje browser a vyžaduje CSRF token (→ 422)
        try:
            resp1 = rancher_session.post(
                f"{url}/v3-public/pingProviders/ping?action=login",
                json={"finalRedirectUrl": f"{url}/dashboard/"},
                timeout=15
            )
            resp1.raise_for_status()
            idp_url = resp1.json().get('idpRedirectUrl')
        except Exception as e:
            raise Exception(f"SAML init selhalo: {e}")

        if not idp_url:
            raise Exception("SAML login: Rancher nevrátil idpRedirectUrl")

        # Krok 2: GET PingFederate login stránka (browser UA pro IdP)
        try:
            resp2 = idp_session.get(idp_url, allow_redirects=True, timeout=15)
        except Exception as e:
            raise Exception(f"SAML login: nelze načíst PingFederate stránku: {e}")

        # Krok 3: Parsovat formulář
        parser = _FormParser()
        parser.feed(resp2.text)

        if not parser.forms:
            raise Exception(
                f"SAML login: přihlašovací formulář nenalezen na {resp2.url} "
                f"(HTTP {resp2.status_code})"
            )

        form = parser.forms[0]
        user_field = next((f for f in form['text_inputs'] if 'user' in f.lower() or 'name' in f.lower() or f == 'pf.username'), None) \
                     or (form['text_inputs'][0] if form['text_inputs'] else None)
        pass_field = next((f for f in form['password_inputs'] if 'pass' in f.lower() or f == 'pf.pass'), None) \
                     or (form['password_inputs'][0] if form['password_inputs'] else None)

        if not user_field:
            raise Exception(f"SAML login: pole pro uživatele nenalezeno (dostupná: {form['text_inputs']})")
        if not pass_field:
            raise Exception(f"SAML login: pole pro heslo nenalezeno (dostupná: {form['password_inputs']})")

        form['inputs'][user_field] = username
        form['inputs'][pass_field] = password

        action_url = urllib.parse.urljoin(resp2.url, form['action'])

        # Krok 4: POST přihlašovacích údajů na PingFederate
        try:
            resp3 = idp_session.post(
                action_url,
                data=form['inputs'],
                allow_redirects=True,
                timeout=30
            )
        except Exception as e:
            raise Exception(f"SAML login: chyba při POST na PingFederate: {e}")

        # Krok 4b: SAML POST binding — PingFederate vrátí HTML stránku s formulářem
        # obsahujícím SAMLResponse, který browser auto-submituje na Rancher ACS.
        # MUSÍ použít rancher_session (nikoliv idp_session) protože:
        # - rancher_session má saml_Rancher_* cookies z kroku 1 (korelace SAML exchange)
        # - rancher_session.verify = bundle → pokrývá localsite-rancher-pro.app.corp
        saml_parser = _FormParser()
        saml_parser.feed(resp3.text)
        saml_form = next(
            (f for f in saml_parser.forms if 'SAMLResponse' in f['inputs']),
            None
        )
        if saml_form:
            saml_action = urllib.parse.urljoin(resp3.url, saml_form['action'])
            try:
                resp3 = rancher_session.post(
                    saml_action,
                    data=saml_form['inputs'],
                    allow_redirects=True,
                    timeout=30
                )
            except Exception as e:
                raise Exception(f"SAML login: chyba při odesílání SAMLResponse na Rancher ACS: {e}")
        else:
            resp3_lower = resp3.text.lower()

            # Krok 4b.1: Detekce chyby přihlašovacích údajů.
            # PingFederate po špatném heslu vrátí login stránku znovu — URL může obsahovat
            # resumeSAML20 (nová session), ale stránka má opět pf.username a pf.pass pole.
            _has_login_form = any(
                'pf.username' in f['text_inputs'] or 'pf.pass' in f['password_inputs']
                for f in saml_parser.forms
            )
            _LOGIN_ERROR_PHRASES = (
                "didn't recognize", "invalid credentials", "incorrect", "please try again",
                "ping-error", "authentication failed", "login failed", "bad credentials",
                "špatné", "neplatné", "nesprávné",
            )
            if _has_login_form and any(p in resp3_lower for p in _LOGIN_ERROR_PHRASES):
                raise Exception("SAML login: špatné přihlašovací údaje (nesprávné jméno nebo heslo)")

            # Krok 4c: Detekce MFA challenge — OTP formulář nebo PingID push pending
            mfa_form = _detect_mfa_form(resp3.text, saml_parser.forms)
            if mfa_form:
                raise MFARequired({
                    'rancher_session': rancher_session,
                    'idp_session':     idp_session,
                    'mfa_action_url':  urllib.parse.urljoin(resp3.url, mfa_form['action']),
                    'mfa_inputs':      dict(mfa_form['inputs']),
                    'mfa_otp_field':   mfa_form['otp_field'],
                    'rancher_url':     url,
                    'verify_ssl':      verify_ssl,
                    'ca_cert':         ca_cert,
                })

            # Krok 4d: PingID push pending — PingFederate čeká na schválení na mobilu.
            # Detekujeme podle URL (resumeSAML20) nebo obsahu stránky.
            # Poznámka: login-error stránka (špatné heslo) TAKÉ vrací resumeSAML20 v URL —
            # proto tu kontrolu děláme AŽ PO detekci login chyby výše.
            PUSH_KEYWORDS = ['push', 'approve', 'pending', 'sent to your', 'pingid',
                             'check your phone', 'mobile app', 'notification', 'authenticate',
                             'approved', 'waiting', 'authenticating', 'ppm_request']
            is_push_pending = (
                'resumesaml' in resp3.url.lower()
                or any(kw in resp3_lower for kw in PUSH_KEYWORDS)
            )
            if is_push_pending:
                # PingFederate vrátil stránku s auto-POST formulářem na PingID authenticator.
                # Formulář se normálně auto-submituje JS (window.onload) — my ho odesíláme ručně.
                # Po odeslání PingID pošle push notifikaci na telefon.
                # pending_url = resumeSAML20 na PingFederate (odkud získáme SAMLResponse po schválení)
                _pending_url = resp3.url   # = resumeSAML20 URL — NIKDY neměnit na pingone.eu URL!
                _page_html   = resp3.text
                _ppm_params  = None        # pro case resend push
                _login_done  = False

                # Hledáme PingID autopost formu (action = pingone.eu/pingid/ppm/auth nebo podobná)
                PINGID_DOMAINS = ('authenticator.pingone.', 'pingid.pingone.', 'pingid.')
                pingid_form = next(
                    (f for f in saml_parser.forms
                     if not f['inputs'].get('SAMLResponse')
                     and any(d in f.get('action', '') for d in PINGID_DOMAINS)),
                    None
                )

                if pingid_form:
                    # Odeslat POST na PingID authenticator → spustí push na telefon.
                    # ppm_request JWT je self-contained, nepotřebuje idp_session cookies.
                    # Zkusíme nejdřív čistou session, pak idp_session.
                    _ppm_url   = pingid_form['action']
                    _ppm_data  = dict(pingid_form['inputs'])
                    _ppm_error = None

                    # Extrahuj returnUrl z ppm_request JWT (base64 payload — nekontrolujeme signaturu)
                    try:
                        import base64 as _b64, json as _json
                        _jwt_parts = _ppm_data.get('ppm_request', '').split('.')
                        if len(_jwt_parts) >= 2:
                            _pad = _jwt_parts[1] + '=' * (-len(_jwt_parts[1]) % 4)
                            _payload = _json.loads(_b64.b64decode(_pad).decode('utf-8', errors='replace'))
                            _return_url = _payload.get('returnUrl')
                            if _return_url:
                                _pending_url = _return_url   # správnější než resp3.url
                    except Exception:
                        pass

                    # Zkus POST — čistá session (ppm_request JWT nepotřebuje cookies)
                    for _sess in (requests.Session(), idp_session):
                        _sess.verify = False
                        _sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
                        try:
                            _pr = _sess.post(_ppm_url, data=_ppm_data,
                                             allow_redirects=True, timeout=20)
                            # Úspěch — push odeslán nebo redirectováno zpět na PingFederate
                            _ppm_params = {'url': _ppm_url, 'data': _ppm_data, 'status': _pr.status_code}
                            break
                        except Exception as _e:
                            _ppm_error = str(_e)

                else:
                    # Žádná PingID forma — zkusíme ostatní formuláře (výběr metody apod.)
                    PUSH_VALUES = {'push', 'pingid_push', 'pingidpush', 'mobile', 'app', 'pingid', '1'}
                    for _form in saml_parser.forms:
                        if 'SAMLResponse' in _form['inputs']:
                            continue
                        _fdata = dict(_form['inputs'])
                        for _rname, _ropts in _form.get('_radio_groups', {}).items():
                            _push_opt = next(
                                (o for o in _ropts if o['value'].lower() in PUSH_VALUES), None
                            )
                            if _push_opt:
                                _fdata[_rname] = _push_opt['value']
                        _faction = urllib.parse.urljoin(resp3.url, _form['action']) if _form['action'] else resp3.url
                        try:
                            _fr = idp_session.post(_faction, data=_fdata, allow_redirects=True, timeout=15)
                            _fp2 = _FormParser()
                            _fp2.feed(_fr.text)
                            _saml2 = next((f for f in _fp2.forms if 'SAMLResponse' in f['inputs']), None)
                            if _saml2:
                                _a2 = urllib.parse.urljoin(_fr.url, _saml2['action'])
                                resp3 = rancher_session.post(_a2, data=_saml2['inputs'],
                                                             allow_redirects=True, timeout=30)
                                _login_done = True
                                break
                            # Pokud redirect vedl na jiný PingFederate resumeSAML → aktualizovat
                            if 'resumesaml' in _fr.url.lower() and _fr.url != resp3.url:
                                _pending_url = _fr.url
                                break
                        except Exception:
                            pass

                if not _login_done:
                    raise PushPending({
                        'rancher_session':  rancher_session,
                        'idp_session':      idp_session,
                        'pending_url':      _pending_url,
                        'rancher_url':      url,
                        'verify_ssl':       verify_ssl,
                        'ca_cert':          ca_cert,
                        'page_html':        _page_html,
                        'ppm_params':       _ppm_params,
                        'ppm_error':        _ppm_error if '_ppm_error' in dir() else None,
                    })
                # _login_done=True → padneme do kroku 5 (extrakce tokenu)
            else:
                all_cookies = list(idp_session.cookies.keys()) + list(rancher_session.cookies.keys())
                raise Exception(
                    f"SAML login: neznámý stav po přihlášení (URL: {resp3.url}, "
                    f"cookies: {all_cookies})"
                )

        # Krok 5: R_SESS cookie z Rancher ACS callbacku
        # Zkontroluj obě sessions (cookie mohl přijít přes redirect v idp_session i rancher_session)
        r_sess = rancher_session.cookies.get('R_SESS') or idp_session.cookies.get('R_SESS')
        if r_sess:
            return r_sess

        # Fallback: token v URL
        m = re.search(r'token=([^&#]+)', resp3.url)
        if m:
            return urllib.parse.unquote(m.group(1))

        if 'login' in resp3.url.lower() or resp3.status_code in (401, 403):
            raise Exception("SAML login: špatné přihlašovací údaje")

        all_cookies = list(idp_session.cookies.keys()) + list(rancher_session.cookies.keys())
        raise Exception(
            f"SAML login: token nezískán (final URL: {resp3.url}, "
            f"cookies: {all_cookies})"
        )

    @classmethod
    def _poll_push_pending(cls, pending_url: str, rancher_session, idp_session,
                           timeout: int = 120) -> requests.Response:
        """
        Polluje PingFederate pending URL dokud uživatel neschválí PingID push notifikaci.
        Vrátí finální HTTP response (po submitu SAMLResponse na Rancher ACS).

        Args:
            pending_url: URL stránky kde PingFederate čeká na push (resumeSAML20/...)
            rancher_session: Session s Rancher cookies (pro ACS callback)
            idp_session:     Session s PingFederate cookies (PF, session cookies)
            timeout:         Max čekací doba v sekundách (default 120)

        Raises:
            Exception: Push odmítnut, vypršel timeout nebo jiná chyba
        """
        import time as _time

        POLL_INTERVAL = 3   # sekund mezi dotazy
        REJECT_WORDS  = ('denied', 'rejected', 'expired', 'error', 'failed',
                         'odmítnuto', 'vypršelo', 'chyba', 'selhalo')

        deadline = _time.time() + timeout
        while _time.time() < deadline:
            _time.sleep(POLL_INTERVAL)
            try:
                resp = idp_session.get(pending_url, allow_redirects=True, timeout=15)
            except Exception:
                continue

            parser = _FormParser()
            parser.feed(resp.text)

            # Hledáme SAMLResponse — push byl schválen
            saml_form = next((f for f in parser.forms if 'SAMLResponse' in f['inputs']), None)
            if saml_form:
                saml_action = urllib.parse.urljoin(resp.url, saml_form['action'])
                try:
                    acs_resp = rancher_session.post(
                        saml_action,
                        data=saml_form['inputs'],
                        allow_redirects=True,
                        timeout=30,
                    )
                    return acs_resp
                except Exception as e:
                    raise Exception(f"SAML push: chyba při odesílání SAMLResponse: {e}")

            # OTP formulář — fallback na TOTP/SMS místo push
            mfa_form = _detect_mfa_form(resp.text, parser.forms)
            if mfa_form:
                raise MFARequired({
                    'rancher_session': rancher_session,
                    'idp_session':     idp_session,
                    'mfa_action_url':  urllib.parse.urljoin(resp.url, mfa_form['action']),
                    'mfa_inputs':      dict(mfa_form['inputs']),
                    'mfa_otp_field':   mfa_form['otp_field'],
                    'rancher_url':     '',
                    'verify_ssl':      True,
                    'ca_cert':         None,
                })

            # Explicitní odmítnutí
            resp_lower = resp.text.lower()
            if any(w in resp_lower for w in REJECT_WORDS) and 'resumesaml' not in resp.url.lower():
                raise Exception("SAML push: push notifikace byla odmítnuta nebo vypršela v PingID")

        raise Exception(
            f"SAML push: timeout {timeout}s — push notifikace nebyla schválena. "
            f"Zkontrolujte telefon nebo zkuste znovu."
        )

    @classmethod
    def _saml_check_push(cls, push_state: dict) -> str:
        """
        Jednorázově ověří, zda uživatel schválil PingID push notifikaci.
        Volá se po kliknutí tlačítka "Schválil jsem" v UI.

        Args:
            push_state: Stav z PushPending.state (sessions + pending_url)

        Returns:
            Bearer token (R_SESS cookie)
        Raises:
            Exception: Push ještě nebyl schválen, odmítnut, nebo jiná chyba
        """
        rancher_session = push_state['rancher_session']
        idp_session     = push_state['idp_session']
        pending_url     = push_state['pending_url']

        try:
            resp = idp_session.get(pending_url, allow_redirects=True, timeout=15)
        except Exception as e:
            raise Exception(f"Chyba při ověření push: {e}")

        parser = _FormParser()
        parser.feed(resp.text)

        # Push schválen → PingFederate vrátil SAMLResponse
        saml_form = next((f for f in parser.forms if 'SAMLResponse' in f['inputs']), None)
        if saml_form:
            saml_action = urllib.parse.urljoin(resp.url, saml_form['action'])
            try:
                acs_resp = rancher_session.post(
                    saml_action,
                    data=saml_form['inputs'],
                    allow_redirects=True,
                    timeout=30,
                )
            except Exception as e:
                raise Exception(f"SAML push: chyba při odesílání SAMLResponse: {e}")

            r_sess = rancher_session.cookies.get('R_SESS') or idp_session.cookies.get('R_SESS')
            if r_sess:
                return r_sess
            m = re.search(r'token=([^&#]+)', acs_resp.url)
            if m:
                return urllib.parse.unquote(m.group(1))
            raise Exception(f"Token nezískán po push schválení (URL: {acs_resp.url})")

        resp_lower = resp.text.lower()

        # Stránka vrátila znovu PingID autopost formu — push ještě nebyl schválen
        PINGID_DOMAINS = ('authenticator.pingone.', 'pingid.pingone.', 'pingid.')
        pingid_form2 = next(
            (f for f in parser.forms
             if not f['inputs'].get('SAMLResponse')
             and any(d in f.get('action', '') for d in PINGID_DOMAINS)),
            None
        )
        if pingid_form2:
            raise Exception(
                "Push ještě nebyl schválen — schvalte notifikaci v PingID aplikaci a zkuste znovu"
            )

        # Page Expired nebo session vypršela
        if 'no longer available' in resp_lower or 'page expired' in resp_lower or 'timed out' in resp_lower:
            raise Exception(
                "Platnost přihlašovacího pokusu vypršela (Page Expired) — klikněte 'Zkusit znovu' a přihlaste se znovu"
            )

        # Explicitní odmítnutí
        if any(w in resp_lower for w in ('denied', 'rejected', 'odmítnuto', 'vypršelo')):
            raise Exception("Push notifikace byla odmítnuta nebo vypršela — zkuste se přihlásit znovu")

        # OTP fallback
        mfa_form = _detect_mfa_form(resp.text, parser.forms)
        if mfa_form:
            raise MFARequired({
                'rancher_session': rancher_session,
                'idp_session':     idp_session,
                'mfa_action_url':  urllib.parse.urljoin(resp.url, mfa_form['action']),
                'mfa_inputs':      dict(mfa_form['inputs']),
                'mfa_otp_field':   mfa_form['otp_field'],
                'rancher_url':     push_state.get('rancher_url', ''),
                'verify_ssl':      push_state.get('verify_ssl', True),
                'ca_cert':         push_state.get('ca_cert'),
            })

        # Push ještě nebyl schválen (stránka stále čeká)
        PUSH_KEYWORDS = ['push', 'approve', 'pending', 'pingid', 'waiting', 'authenticating']
        if any(kw in resp_lower for kw in PUSH_KEYWORDS) or 'resumesaml' in resp.url.lower():
            raise Exception("Push ještě nebyl schválen — schvalte notifikaci v PingID a zkuste znovu")

        raise Exception(f"Neočekávaná odpověď po push schválení (URL: {resp.url})")

    @classmethod
    def _saml_login_complete(cls, mfa_state: dict, otp_code: str) -> str:
        """
        Dokončí SAML přihlášení po ověření MFA OTP kódem.

        Args:
            mfa_state: Mezistav z MFARequired.state (sessions, form data)
            otp_code:  OTP kód zadaný uživatelem

        Returns:
            Bearer token (R_SESS cookie)
        Raises:
            Exception: Při nesprávném OTP nebo jiné chybě
        """
        rancher_session = mfa_state['rancher_session']
        idp_session     = mfa_state['idp_session']
        action_url      = mfa_state['mfa_action_url']
        inputs          = dict(mfa_state['mfa_inputs'])
        otp_field       = mfa_state['mfa_otp_field']

        inputs[otp_field] = otp_code

        try:
            resp = idp_session.post(
                action_url,
                data=inputs,
                allow_redirects=True,
                timeout=30,
            )
        except Exception as e:
            raise Exception(f"SAML MFA: chyba při odeslání OTP: {e}")

        parser = _FormParser()
        parser.feed(resp.text)
        saml_form = next((f for f in parser.forms if 'SAMLResponse' in f['inputs']), None)

        if not saml_form:
            resp_lower = resp.text.lower()
            if any(w in resp_lower for w in ('invalid', 'incorrect', 'wrong', 'nesprávn',
                                              'chybn', 'otp', 'passcode', 'verification')):
                raise Exception("SAML MFA: nesprávný OTP kód — zkuste znovu")
            raise Exception(f"SAML MFA: SAMLResponse nenalezena po OTP (URL: {resp.url})")

        saml_action = urllib.parse.urljoin(resp.url, saml_form['action'])
        try:
            resp_acs = rancher_session.post(
                saml_action,
                data=saml_form['inputs'],
                allow_redirects=True,
                timeout=30,
            )
        except Exception as e:
            raise Exception(f"SAML MFA: chyba při odesílání SAMLResponse na Rancher ACS: {e}")

        r_sess = rancher_session.cookies.get('R_SESS') or idp_session.cookies.get('R_SESS')
        if r_sess:
            return r_sess

        m = re.search(r'token=([^&#]+)', resp_acs.url)
        if m:
            return urllib.parse.unquote(m.group(1))

        raise Exception(f"SAML MFA: token nezískán po OTP ověření (URL: {resp_acs.url})")

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test připojení k Rancher API

        Returns:
            Tuple[bool, str]: (úspěch, zpráva)
        """
        try:
            response = self.session.get(
                f"{self.rancher_url}/v3",
                verify=self.verify_ssl,
                timeout=10
            )
            response.raise_for_status()
            return True, "Připojení k Rancher úspěšné"
        except requests.exceptions.SSLError:
            return False, "SSL certifikát není platný. Zkuste verify_ssl=False"
        except requests.exceptions.ConnectionError:
            return False, f"Nelze se připojit k {self.rancher_url}"
        except requests.exceptions.Timeout:
            return False, "Timeout při připojení k Rancher"
        except requests.exceptions.HTTPError as e:
            return False, f"HTTP chyba: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return False, f"Chyba připojení: {str(e)}"

    def list_clusters(self) -> List[Dict]:
        """
        Získat seznam všech Kubernetes clusterů v Rancher

        Returns:
            List[Dict]: Seznam clusterů s jejich metadaty
        """
        try:
            response = self.session.get(
                f"{self.rancher_url}/v3/clusters",
                verify=self.verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            clusters = []
            for cluster in data.get('data', []):
                clusters.append({
                    'id': cluster.get('id'),
                    'name': cluster.get('name'),
                    'state': cluster.get('state'),
                    'version': cluster.get('version', {}).get('gitVersion', 'N/A'),
                    'provider': cluster.get('provider', 'unknown'),
                    'node_count': len(cluster.get('nodePoolIds', [])),
                })

            return clusters
        except Exception as e:
            print(f"Chyba při získávání clusterů: {e}")
            return []

    def get_kubeconfig(self, cluster_id: str, ttl_ms: int = 3600000) -> Optional[str]:
        """
        Získat kubeconfig pro konkrétní cluster s platným tokenem.
        Volá Rancher generateKubeconfig akci – vyžaduje oprávnění 'generateKubeconfig' na clusteru.

        Args:
            cluster_id: ID clusteru v Rancher
            ttl_ms: Time-to-live tokenu v milisekundách (default 1 hodina)

        Returns:
            Optional[str]: Kubeconfig jako string nebo None při chybě

        Raises:
            Exception: Při HTTP chybě (403, 404, …) s detailní zprávou z Rancher API
        """
        url = f"{self.rancher_url}/v3/clusters/{cluster_id}?action=generateKubeconfig"
        # Posílat prázdné tělo – starší verze Rancher neumí JSON s TTL
        response = self.session.post(
            url,
            json={},
            verify=self.verify_ssl,
            timeout=30
        )

        if not response.ok:
            try:
                body = response.json()
                detail = body.get('message') or body.get('Message') or response.text
            except Exception:
                detail = response.text
            raise Exception(
                f"generateKubeconfig selhalo [{response.status_code}] pro cluster {cluster_id}: {detail}"
            )

        data = response.json()
        kubeconfig = data.get('config')
        if not kubeconfig:
            raise Exception(f"Rancher nevrátil 'config' ve odpovědi generateKubeconfig pro {cluster_id}")

        # Pokud je SSL verifikace vypnuta, přidat insecure-skip-tls-verify do kubeconfig
        # aby kubernetes klient také neověřoval certifikát Rancher proxy
        if not self.verify_ssl:
            kubeconfig = self._patch_kubeconfig_insecure(kubeconfig)

        return kubeconfig

    def _patch_kubeconfig_insecure(self, kubeconfig_str: str) -> str:
        """Přidat insecure-skip-tls-verify do všech clusterů v kubeconfig YAML."""
        try:
            kc = yaml.safe_load(kubeconfig_str)
            for cluster_entry in kc.get('clusters', []):
                cluster_entry.setdefault('cluster', {})
                # Odebrat certificate-authority-data, přidat insecure flag
                cluster_entry['cluster'].pop('certificate-authority-data', None)
                cluster_entry['cluster']['insecure-skip-tls-verify'] = True
            return yaml.dump(kc, default_flow_style=False)
        except Exception:
            # Při chybě parsování vrátit originál
            return kubeconfig_str

    def save_kubeconfig_to_temp(self, cluster_id: str) -> Optional[str]:
        """
        Uložit kubeconfig do dočasného souboru

        Args:
            cluster_id: ID clusteru

        Returns:
            Optional[str]: Cesta k dočasnému souboru nebo None
        """
        kubeconfig = self.get_kubeconfig(cluster_id)
        if not kubeconfig:
            return None

        try:
            # Vytvoření dočasného souboru
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(kubeconfig)
                temp_path = f.name

            return temp_path
        except Exception as e:
            print(f"Chyba při ukládání kubeconfig: {e}")
            return None

    def get_cluster_info(self, cluster_id: str) -> Optional[Dict]:
        """
        Získat detailní informace o clusteru

        Args:
            cluster_id: ID clusteru

        Returns:
            Optional[Dict]: Informace o clusteru nebo None
        """
        try:
            response = self.session.get(
                f"{self.rancher_url}/v3/clusters/{cluster_id}",
                verify=self.verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Chyba při získávání informací o clusteru: {e}")
            return None

    def generate_proxy_kubeconfig(self, cluster_id: str, cluster_name: str = None) -> str:
        """
        Vygenerovat kubeconfig pro přístup přes Rancher proxy.

        Používá username/password (Basic Auth) – Rancher proxy endpoint
        /k8s/clusters/<id> akceptuje Basic Auth stejně jako Rancher API.
        Bearer token z API klíče Rancher ODMTÍ pro proxy endpoint
        (vrací X-Api-Cattle-Auth: false / system:unauthenticated).

        Args:
            cluster_id: ID clusteru v Rancher (např. "c-xxxxx")
            cluster_name: Jméno clusteru (volitelné)

        Returns:
            str: Kubeconfig jako YAML string
        """
        name = cluster_name or cluster_id

        kubeconfig = {
            'apiVersion': 'v1',
            'kind': 'Config',
            'clusters': [{
                'name': name,
                'cluster': {
                    'server': f'{self.rancher_url}/k8s/clusters/{cluster_id}',
                }
            }],
            # Autentifikace: bearer_token (z username/password login) nebo Basic Auth (API key)
            'users': [{
                'name': f'{name}-user',
                'user': (
                    {'token': self.bearer_token}
                    if self.bearer_token
                    else {'username': self.access_key, 'password': self.secret_key}
                )
            }],
            'contexts': [{
                'name': name,
                'context': {
                    'cluster': name,
                    'user': f'{name}-user'
                }
            }],
            'current-context': name
        }

        if self.verify_ssl and isinstance(self.verify_ssl, str) and os.path.exists(self.verify_ssl):
            with open(self.verify_ssl, 'rb') as f:
                ca_data = base64.b64encode(f.read()).decode()
            kubeconfig['clusters'][0]['cluster']['certificate-authority-data'] = ca_data
        elif not self.verify_ssl:
            kubeconfig['clusters'][0]['cluster']['insecure-skip-tls-verify'] = True

        return yaml.dump(kubeconfig, default_flow_style=False)

    def kubeconfig_has_exec_credentials(self, kubeconfig_str: str) -> bool:
        """Zkontrolovat, zda kubeconfig používá exec: credentials (kubectl plugin).
        Kubernetes Python klient exec nespustí, pokud není CLI dostupné."""
        try:
            kc = yaml.safe_load(kubeconfig_str)
            for user_entry in kc.get('users', []):
                if 'exec' in user_entry.get('user', {}):
                    return True
        except Exception:
            pass
        return False
