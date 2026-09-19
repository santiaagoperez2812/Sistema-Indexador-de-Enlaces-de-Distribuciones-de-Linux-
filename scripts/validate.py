import glob
import sys
import asyncio
import httpx
import yaml

# Encabezado para evitar que servidores bloqueen la petición por considerarla bot genérico
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LinuxDistroIndexBot/1.0; +https://github.com/)"
}

TIMEOUT = 10.0  # segundos por petición


async def check_url(semaphore: asyncio.Semaphore, client: httpx.AsyncClient, distro_name: str, field: str, url: str):
    if not url or not url.startswith("http"):
        return {"status": "SKIPPED", "distro": distro_name, "field": field, "url": url, "error": "URL inválida o vacía"}

    async with semaphore:
        try:
            # Primero intentamos con HEAD por rapidez y menor consumo de datos
            response = await client.head(url, follow_redirects=True, timeout=TIMEOUT)
            
            # Algunos sitios rechazan peticiones HEAD con 403/405; si ocurre, reintentamos con GET
            if response.status_code in (403, 405):
                response = await client.get(url, follow_redirects=True, timeout=TIMEOUT)

            if response.status_code < 400:
                return {"status": "OK", "distro": distro_name, "field": field, "url": url, "code": response.status_code}
            else:
                return {"status": "FAIL", "distro": distro_name, "field": field, "url": url, "code": response.status_code}

        except httpx.RequestError as exc:
            return {"status": "ERROR", "distro": distro_name, "field": field, "url": url, "error": str(exc)}


async def main():
    files = glob.glob("data/*.yaml")
    if not files:
        print("❌ No se encontraron archivos YAML en la carpeta data/")
        sys.exit(1)

    print(f"🔍 Analizando {len(files)} distribuciones...")

    # Semáforo para limitar concurrencia a un máximo de 15 peticiones simultáneas
    semaphore = asyncio.Semaphore(15)
    tasks = []

    async with httpx.AsyncClient(headers=HEADERS, verify=True) as client:
        for filepath in files:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            distro_name = data.get("name", filepath)

            # 1. Enlaces generales
            links = data.get("links", {})
            for key, url in links.items():
                tasks.append(check_url(semaphore, client, distro_name, f"links.{key}", url))

            # 2. Enlace de verificación
            verification = data.get("verification", {})
            if "signatures_url" in verification:
                tasks.append(check_url(semaphore, client, distro_name, "verification.signatures_url", verification["signatures_url"]))

        results = await asyncio.gather(*tasks)

    # Procesar y mostrar reporte
    failed = [r for r in results if r["status"] in ("FAIL", "ERROR", "SKIPPED")]
    success = [r for r in results if r["status"] == "OK"]

    print("\n" + "=" * 60)
    print(f"📊 Resumen de validación: {len(success)} enlaces OK | {len(failed)} fallos")
    print("=" * 60)

    if failed:
        print("\n⚠️ Enlaces con problemas detectados:")
        for f in failed:
            detalle = f"Código {f.get('code')}" if "code" in f else f.get("error")
            print(f"  ❌ [{f['distro']}] {f['field']}: {f['url']} -> {detalle}")
        sys.exit(1)
    else:
        print("\n✅ ¡Todos los enlaces oficiales respondieron correctamente!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())