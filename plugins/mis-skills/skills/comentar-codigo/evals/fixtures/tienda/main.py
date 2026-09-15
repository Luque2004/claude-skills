import json
import sys
from inventario import Inventario, cargar_productos


def parsear_args(argv):
    if len(argv) < 2:
        print("Uso: main.py <comando> [args]")
        sys.exit(1)
    comando = argv[1]
    resto = argv[2:]
    return comando, resto


def main():
    comando, args = parsear_args(sys.argv)
    inv = Inventario(cargar_productos("datos.json"))

    if comando == "listar":
        for p in inv.listar():
            print(f"{p['sku']:10} {p['nombre']:25} {p['stock']:5} {p['precio']:8.2f}")
    elif comando == "vender":
        sku, cantidad = args[0], int(args[1])
        try:
            total = inv.vender(sku, cantidad)
            print(f"Vendido. Total: {total:.2f}")
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(2)
    elif comando == "reponer":
        bajos = inv.bajo_stock(umbral=5)
        if not bajos:
            print("Nada que reponer")
        for p in bajos:
            print(f"Reponer {p['sku']} ({p['stock']} unidades)")
    else:
        print(f"Comando desconocido: {comando}")
        sys.exit(1)

    with open("datos.json", "w") as f:
        json.dump(inv.productos, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
