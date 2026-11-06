import os
import json

COOKIES_DATA = {
    "youtube.txt": [
        {"domain": ".youtube.com", "name": "VISITOR_PRIVACY_METADATA", "value": "CgJJThIEGgAgZg%3D%3D", "expirationDate": 1809536217},
        {"domain": ".youtube.com", "name": "__Secure-3PSID", "value": "g.a000Egk46zztKjTe49zTLwM7182DKZeZT-GmgQDeitJRSmhlF3KBRLMW6r1psbtR0RFhUTjxEwACgYKATQSARMSFQHGX2Miz09XsRcpiXfhf88enttNJhoVAUF8yKrSFtRuM054L2NG4gjZuM7J0076", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "GPS", "value": "1", "expirationDate": 1793985000},
        {"domain": ".youtube.com", "name": "SIDCC", "value": "APD_SKHQiveoj7pbY1B-e3fLv0Dt43v5m1gJQP5Nc8W4omDpRmdYb7qLDhd0QAqUPMDCYHS_", "expirationDate": 1825520220},
        {"domain": ".youtube.com", "name": "YSC", "value": "9Dqu379GhSk", "expirationDate": 0},
        {"domain": ".youtube.com", "name": "SID", "value": "g.a000Egk46zztKjTe49zTLwM7182DKZeZT-GmgQDeitJRSmhlF3KBf-7ca59N8sEC7KgYxm-L9gACgYKAX0SARMSFQHGX2MihL_pftsEDegR2r9hGEJlExoVAUF8yKoj64dwLc4Vir_NJwXkF-gd0076", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "__Secure-1PSIDTS", "value": "sidts-CjQBnJZzanSlWaSeWiRlvUygojlpb5hR7zxQhqdrpyt2CerSa2RcRd9rM2pr3dXSlEWaWMEsEAA", "expirationDate": 1825519256},
        {"domain": ".youtube.com", "name": "SAPISID", "value": "5mxiUK3s1akuiDBh/AOAh3IoJqQTknptBb", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "__Secure-1PSIDCC", "value": "APD_SKFEIGVr3xwMESCOTvBPUq46bsQPRgt3eM0PCnP_Eu9TL3oLAPFYsDwPQ-XBBPaVtXbG", "expirationDate": 1825520220},
        {"domain": ".youtube.com", "name": "SSID", "value": "ATHa9Q0uOeK99pyUj", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "__Secure-1PAPISID", "value": "5mxiUK3s1akuiDBh/AOAh3IoJqQTknptBb", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "__Secure-1PSID", "value": "g.a000Egk46zztKjTe49zTLwM7182DKZeZT-GmgQDeitJRSmhlF3KBzglZnqbkQLaX7qDE-zgjBQACgYKAecSARMSFQHGX2MiUjEEJYFr57mGBFTCNWQePBoVAUF8yKpdzfu5n0_k6XOc1F_tgpOp0076", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "__Secure-3PAPISID", "value": "5mxiUK3s1akuiDBh/AOAh3IoJqQTknptBb", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "__Secure-3PSIDCC", "value": "APD_SKEEAwjuEQjmBYHp6LJp6nX3PZp7jXGjUC2-4PRibUaBz4ZzB0vpnCaKHQdD7fckLSOR", "expirationDate": 1825520220},
        {"domain": ".youtube.com", "name": "__Secure-3PSIDTS", "value": "sidts-CjQBnJZzanSlWaSeWiRlvUygojlpb5hR7zxQhqdrpyt2CerSa2RcRd9rM2pr3dXSlEWaWMEsEAA", "expirationDate": 1825519256},
        {"domain": ".youtube.com", "name": "__Secure-YNID", "value": "CtoBCAUSjAEBDB6PDMggTN-P0Yv9rAhHiq6eE54X5bBy-6LBQxXuLGiF2dXpV-BdlQwk5AoH4Rq8zAu9sB0vFk1Br-eKdwImEhWzbB1XgAm-ZHNfQyTHmEzjN5eZdlCoo_va-e7weI_uAcBrFFO4gRjCjK9kuSTpL6mBstS-l3FHz6DYDZf_0yWJVQ1EAqcpEO49aygFMkUBHFj1au9F1DVsCNdctutOes_5hYcUPtHkifxlt92vd7Yk6Ztl4kJpSRaXUPvjnl48Zu0qrVOGUpm3IsnRGSlalhOFAws", "expirationDate": 1809535200},
        {"domain": ".youtube.com", "name": "APISID", "value": "69FXIJOKsSb7Ay74/Avzrez4hKEVOXM6Ps", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "HSID", "value": "AxyD5vJ-_0-hmSJZK", "expirationDate": 1828543256},
        {"domain": ".youtube.com", "name": "LOGIN_INFO", "value": "AFmmF2swRAIgcSf3PuEA-P2yUiFL2W-ryZc9LkxzGNZtbYa0v9nipFwCIFpLKA1CYkyvYgIaNGCjethamNZ1-6nmfD89NdkVxYTb:QUQ3MjNmeHZUTWtPSGpkZGotMUxINkxmVU52RGd3MU5LRFZzM2w4TV9uMWlpSy1XSjc4c0RhSEdjNEo2WU82Wl9Lc2NzRWZUMks0S2lsTUVLMm5YRzlFZmRIQVk0TFNueVFuaXVlVHJXbUM1VkpteVhhUU5rNkdlaEdVSUJRSFZEX0I0X2g0NEhFQnpKTkM1eVNYUWpzVDNMT3dlUWc0T2p3", "expirationDate": 1828543257},
        {"domain": ".youtube.com", "name": "PREF", "value": "f6=40000000&tz=Asia.Kolkata&f4=4000000", "expirationDate": 1828543550},
        {"domain": ".youtube.com", "name": "VISITOR_INFO1_LIVE", "value": "cpgrYatvHuo", "expirationDate": 1809536217}
    ],
    "instagram.txt": [
        {"domain": ".instagram.com", "name": "ps_n", "value": "1", "expirationDate": 1828543792},
        {"domain": ".instagram.com", "name": "datr", "value": "MQXuak-DzxEIpwnZg6a2L6Qn", "expirationDate": 1828543792},
        {"domain": ".instagram.com", "name": "ds_user_id", "value": "68193481076", "expirationDate": 1801759897},
        {"domain": ".instagram.com", "name": "csrftoken", "value": "IRoCbVXA3qMj8Kh3T9l2tg", "expirationDate": 1828543897},
        {"domain": ".instagram.com", "name": "ig_did", "value": "83A00985-C5A6-4DA1-97F4-E6F1B9A62206", "expirationDate": 1825519792},
        {"domain": ".instagram.com", "name": "ps_l", "value": "1", "expirationDate": 1828543792},
        {"domain": ".instagram.com", "name": "wd", "value": "423x780", "expirationDate": 1794588700},
        {"domain": ".instagram.com", "name": "mid", "value": "au4FMQABAAHOxL9hT1fX8odVj4Km", "expirationDate": 1828543794},
        {"domain": ".instagram.com", "name": "sessionid", "value": "68193481076%3AbLR0x7fgumtWDg%3A23%3AAYmNJGnXLDOoHgUNvBKDQhBQ5f_vKJ1e9X04CIGblg", "expirationDate": 1825519853},
        {"domain": ".instagram.com", "name": "dpr", "value": "3", "expirationDate": 1794588653},
        {"domain": ".instagram.com", "name": "rur", "value": "EAG%2C17841468192284185%2C1795193502%3A01ff90d4ec31ef9c1a71042c9f4ae76dfb864f519d64898a5755aa09e68c516faa462090", "expirationDate": 0}
    ],
    "pinterest.txt": [
        {"domain": ".pinterest.com", "name": "_b", "value": "\"AZqQCMdXuftE3ZnGecfc9rH4lsE1fYSIroKN6enhckdqoZfcwmLBP3BecjZq8YHhysY=\"", "expirationDate": 1828543948},
        {"domain": ".pinterest.com", "name": "_pinterest_sess", "value": "TWc9PSZhSHdTckE4ZXFwakJuK1FvdnozNVBKZFd1TzVrYThSQTFmM2Z2SFFKeVFZS3lkMWp4TmVHMjNiTWxzdEN0M25JM2hXSlBTN3l0VlV3UHVBRUlGcTdLZm8wNkVVMi83RVgveUtYa3oyekYxVHdESmJDTUZYclI1d2lCVG9IL25SN0ZpTHZmMk9OUk1sL2NlNWtXTC91anRRNEVwckJzbmplS2l5VmZKYVp1c0JBbndXeXpMR3dPcFRQdFNuZVgzeDNudXFhR2xYSWsvaTg0dzFPWGFiM3E2RzRFV0hMZmJUUllQUnpibytGSTVrTzIwZXhFTEo1OUJtYVFTWjk1TFI4REcrRHlGNlJkZjQ0MHVjOW9OUm51WWRzMUpIbmZXcjY3V3JHMUdiVk5RV2JFKzlWbDU4bCtOT2Q2S0I5WEJndXNnOXN5Myt1bHpTT3lYRitqUGFra3I3NzZuTnNzRlJvWUtacnphUmQ5Q04zMEwyZFRxNFZJSDhRQzFWTHJQUzNYUVVhL2c1Y0pyanQ0ajd1OGxNRzZIOHdDMjJ0ZmNQTytLSlFmYTFIazIvSjYycDVEMGl3cXV6dEQ2cnVaL3RUQS9mNVcwd3NwQ1Y0ZFp5Ymx3RGdSeTkvbXlYVGNLYno1S0M1UFJVUjBVUXJMRTc0VWl1OVo3V05Ic0tYK2g3STlPaU9MMTRHZDU4eU9BQ2VQb1NrWEF4WUFzOUVKaXhsQVgrUTlvSE1LR0dyNmZQZ3hETmpCeG5KbkNWNWFyeUVBcitqaGdEREVOanYxUzdHYjVrbFR2aDhtTU1EOFpMcGpqc2x6YXVyY2Z0OGwyRStFc2wzU21BUHZ2Z3JmU2txZDRsOGJjNUJESENmbXhwVy9DcUczVEc3bzcxdFV5azFKSzc2VGpNLzJEc2xVc2Evb1lIY0JBblZ2cjAxUTEwY1BIUFBiUHJIdmNEakdqZFgrSHlQM3BzZXFabGR0ZXhURi9BMDBDR29rNFpIK05VSzY1Zm84UkZobWkvbVlnSFlQa3llaWdWTVQrQUhLYitSU2FLSWlEODVXT1VldG5rbDRpUVZIWEVvTEMrdlNsZjdaTVlDNHJFdENHTC8xaTBFVmxYbm4yTjdGam1WemhKZks1M3lkYythL0YvTnp5SzZiZUNyYmEwT1F2dGxLanVjNVhkNnkvY2NvMXNTL2l4VjZHTEdVVUlEYjh6SHpJa1ZFZk41TnFzdWhkUVVDM2ttalVhTW83WitJclVmYUlQb2psTnR5UGkwa0hxRmNpR1R2Q2VYaklkbXBCK3hlNVQxNGNPZ0ZaTFBTbGxmQ0tyM0hNSW9jOVZGQUkxMlZ4alpoQ3p0dUJtSVRESzNRSzBsZ2lmckVXUlE2QndzakZ5bGpYSDUrWXBrcC9KZStmM3RaZHlqRXZUTE50L2VHcGYydFBzM0pobC9CRzNIM3ZPcW0zRUovdm5pTzV5ZWtNSThucm53THUxZWI2Qm9ab1N4YUwvTGwrSHlzWDlzZmF3T2o0dEtiUmhQNW56cVZDNVVEeDRUeUdIWWI5SXBFSVB4L1hSTHZDdFBFVXNQQmhxVEU3Slp4Y1NTbmNnMUxkY2h2M1NFcWZZOHkzWGNUSFpnY0FHWnord3ZFNStrN2hGc3J2ekhnbjNMNXFoNW1EUEhjbmtTYTVveVdnNlJPaXJIS291cDd3N25wYUMvL2RzYWZWbTNOV1hybndoR0NrRG1KUmpOTmFCL0VaSVNxSy9wWUJ1a09jbjE3elNaWHJ3WitrT0duZ0xrcHFWd0trSFkmaHhCdDNCbXBvTURJT3ZlR1llVHRHY01VL1hrPQ==", "expirationDate": 1825088000},
        {"domain": ".pinterest.com", "name": "__Secure-s_a", "value": "RVRUUEVlVGRFZVl6OVprSE5pU1dscGp5TlJhMThHMmp2cU00VzJzWFF6YXpUS2dsZnRWZnJtb05BV1k4cTlkK2pNWG9KVi9TUnFYNW1NaDRxVk1VYmx0KzFTRC8zZldCSWhQTTZZUTBrc0RldmFsNXV6ZVhHVEhwVzNSYXJRUjRUa2RDdWxLUVh0Rk9xRzFNRHVLZCs1S0dsbHFwV1RaQ0ZUZ011WnV3ZDg4V2FheGM0RFNaTjJrZWdjR0V5VVF6SHlBWjZkd1RFeHZ6Z1BwVlhoeE5xdFRCSkNqelRKTWNzRGJZR1grUTJMMHV0WERrU3JCajBJdGhMYXp5T1M3RzUvYmF3UEg0YSt3cWhNYk9DSDlkVGx2Nnp2YmllWG1NOGZOOTNuT01EOFdYSDE0YVhJRFBhMkZkTnE1NmZKZnE2am1aMDRzeWVNWUx4bVVPVGdtSHJWNjBwQlNxSjdCaDYvTC9tZUwwbkxpOU9GTUw1KzdXWGlCRFZCRHBpejhVSEJaNHVOWnlVQk5FeDFKT2Z6Sk1JakpWVW1VeGNDVllNVGxKZGd3WEt0bXhkTHVkY2lBL2xhUWFRbEpzcFBuWEhEQ0xweE80K0ZVM0xJYjFHNmwzTzRtTnQvVnBtN3NNdHR2NjNDaVZRUTMxNkNXWGxPNXQ5STFtVjlMbWs1YW9zQXVCb1NkQ2N1S1NRTm90c0R1ZjF2RUVHdjQ5Y2lZb2N6M1VBSENscWozUkZucGZlek15SHJVajQySXNTVlJVU2Nld2JXVEpLZ0pGK1RuTHNHR3FMUnptNUZYdkZVY2loMlRPMTl1QWU5WENIS0lmRUJhTzhPWlVGeG1qMnZRRVRIcExSU0JEOUcrQTlxUGhZR1VTU3NneTUvMEdiK1BjYS81UkZ4TnBxYzRvWW9DOWFyNnNqSmE4cSthdVQrYXVvVGRabUhlanBESWFZYkI1a29KT1R5aHFhdklwSzlFaFBGTmlmRHlwaDVTdnhLMXNxMDYxL2dHTnVzUit5NmViNUt3Q0hkS0dYVkF6eTN0RHFGU3NNQk5LdTJiTFZhYXFSWHIwL2llc29qZU9LbkJsOWdWamdXWmRBQmxjZnRHdUJkZjJGKzNCWGpqa0JNY3F3dGlGZTVuMzNTTWZGRkRiOW5tR0htTXpqN2dSbHBGM3VwdG1ZcjVmSUx4TW5BQ1RMTFRZdEpHVFJ5ZjJ1ODlQZnV0VDE3Y2N1cVVLeXpPckRYZmQvTkVjUkVUV01qYUZLTkMwbWNaQTFONXhyQy8xQWhGditvVWNHajFpMXFUYUM1VHpvZXpLS1pzQnFwRGlGa3RVUGszYmloUT0mOGFQVkp5V0x0ckRJa3NreUhJaTR6S1V3eDBrPQ==", "expirationDate": 1825088000},
        {"domain": ".pinterest.com", "name": "_auth", "value": "1", "expirationDate": 1825088000},
        {"domain": "in.pinterest.com", "name": "csrftoken", "value": "8bdbaef8e1be8c5e17b137450e2ac4d0", "expirationDate": 1825519946}
    ],
    "x.txt": [
        {"domain": ".x.com", "name": "auth_token", "value": "5574f6bf59968d32d1c6ce18ca105bd917bc5d9b", "expirationDate": 1825520165},
        {"domain": ".x.com", "name": "ct0", "value": "a967405b67d7470b3e02b02ad8dc4038e3b6479ff905f15a8218d2b1e6c48a88fb3aafbec0315eaea0fdc96b6555fa627b100769a28458e235644573d7bd469040caa32bfdf450ecbfcbe0f680e4ec94", "expirationDate": 1828544167},
        {"domain": ".x.com", "name": "twid", "value": "u%3D1504164685587038210", "expirationDate": 1825520170},
        {"domain": ".x.com", "name": "guest_id", "value": "v1%3A179398404823622652", "expirationDate": 1828544047}
    ]
}

os.makedirs("cookies", exist_ok=True)

for filename, cookies in COOKIES_DATA.items():
    filepath = os.path.join("cookies", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for c in cookies:
            domain = c["domain"]
            include_sub = "TRUE" if domain.startswith(".") else "FALSE"
            path = "/"
            secure = "TRUE"
            expiry = str(int(c.get("expirationDate", 0)))
            name = c["name"]
            val = c["value"]
            f.write(f"{domain}\t{include_sub}\t{path}\t{secure}\t{expiry}\t{name}\t{val}\n")
    print(f"Created: {filepath}")
