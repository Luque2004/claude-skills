import json
import re

SKU_RE = re.compile(r"^[A-Z]{3}-\d{4}$")
IVA = 0.21


def cargar_productos(ruta):
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    validos = []
    for p in datos:
        if not SKU_RE.match(p.get("sku", "")):
            continue
        if p.get("stock", 0) < 0:
            p["stock"] = 0
        validos.append(p)
    return validos


class Inventario:
    def __init__(self, productos):
        self.productos = productos
        self._por_sku = {p["sku"]: p for p in productos}

    def listar(self):
        return sorted(self.productos, key=lambda p: p["nombre"].lower())

    def vender(self, sku, cantidad):
        p = self._por_sku.get(sku)
        if p is None:
            raise ValueError(f"SKU inexistente: {sku}")
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser positiva")
        if p["stock"] < cantidad:
            raise ValueError(f"Stock insuficiente ({p['stock']} disponibles)")
        p["stock"] -= cantidad
        base = p["precio"] * cantidad
        descuento = 0.1 if cantidad >= 10 else 0
        return base * (1 - descuento) * (1 + IVA)

    def bajo_stock(self, umbral):
        return [p for p in self.productos if p["stock"] <= umbral]
