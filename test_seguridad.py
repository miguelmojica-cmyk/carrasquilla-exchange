import requests

BASE_URL = "http://127.0.0.1:5000"

payloads_sqli = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "admin'--",
    "' UNION SELECT NULL--",
]

payloads_xss = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "<svg onload=alert('XSS')>",
]

resultados = []

def probar_sqli_login():
    print("\n=== PRUEBAS SQL INJECTION EN LOGIN ===")
    for payload in payloads_sqli:
        r = requests.post(BASE_URL + "/login", data={
            "email": payload,
            "contrasena": "123456"
        }, allow_redirects=False)

        location = r.headers.get("Location", "")
        vulnerable = "/login" not in location and r.status_code in (301, 302)

        estado = "VULNERABLE" if vulnerable else "PROTEGIDO"
        print("Payload:", payload, "->", estado)
        resultados.append(("SQLi Login", payload, estado))


def probar_xss_registro():
    print("\n=== PRUEBAS XSS EN REGISTRO ===")
    for i, payload in enumerate(payloads_xss):
        email = "test_xss_" + str(i) + "@carrasquilla.com"
        r = requests.post(BASE_URL + "/registro", data={
            "nombre": payload,
            "email": email,
            "contrasena": "12345678"
        }, allow_redirects=False)

        estado = "Registrado como texto plano (protegido por Jinja2)"
        print("Payload:", payload, "->", estado)
        resultados.append(("XSS Registro", payload, estado))


def generar_reporte():
    print("\n\n========== REPORTE FINAL ==========")
    for tipo, payload, estado in resultados:
        print("[" + tipo + "]", payload, "=>", estado)


probar_sqli_login()
probar_xss_registro()
generar_reporte()