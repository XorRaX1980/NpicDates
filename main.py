import csv
import mimetypes
import io
import json
import re
try:
    import threading
except Exception:
    threading = None
import unicodedata
import flet as ft
from datetime import datetime, timedelta
import os
import tempfile
from pathlib import Path
try:
    import webbrowser
except Exception:
    webbrowser = None
from typing import Dict, List, Optional, Any

# Fix MIME types for web (mjs/wasm)
mimetypes.add_type("application/javascript", ".mjs")
mimetypes.add_type("application/wasm", ".wasm")

# ============ STORAGE SERVICE ============
class StorageService:
    """Abstracción de almacenamiento compatible con Web, Android y Desktop."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.is_web = page.web if hasattr(page, 'web') else False
        self.storage_key = "npic_memory_dates_data"
        # Storage compatible con distintas plataformas/versions
        self._storage = None
        if self.is_web:
            for attr in ("client_storage", "storage", "session_storage"):
                candidate = getattr(self.page, attr, None)
                if candidate is not None:
                    self._storage = candidate
                    break
        self.data: Dict[str, Any] = {
            "equipos": [],
            "mantenimientos": [],
            "tipos": [],
        }
        
    def load(self) -> bool:
        """Carga datos desde el almacenamiento (web o archivo)."""
        try:
            if self.is_web:
                # Modo web: usar client_storage
                if self._storage is None:
                    self._initialize_default_data()
                else:
                    stored = self._storage.get(self.storage_key)
                    if stored:
                        self.data = json.loads(stored)
                    else:
                        self._initialize_default_data()
            else:
                # Modo desktop/móvil: usar archivo JSON
                try:
                    docs_dir = Path.home() / "Documents" / "NPICMemoryDates"
                    docs_dir.mkdir(parents=True, exist_ok=True)
                    json_file = docs_dir / "npic_data.json"
                    
                    if json_file.exists():
                        with open(json_file, 'r', encoding='utf-8') as f:
                            self.data = json.load(f)
                    else:
                        self._initialize_default_data()
                except Exception:
                    self._initialize_default_data()
            return True
        except Exception as e:
            print(f"Error cargando datos: {e}")
            self._initialize_default_data()
            return False
    
    def save(self) -> bool:
        """Guarda datos en el almacenamiento (web o archivo)."""
        try:
            if self.is_web:
                # Modo web: usar client_storage
                if self._storage is not None:
                    self._storage.set(self.storage_key, json.dumps(self.data))
                else:
                    # Sin storage disponible: mantener en memoria
                    pass
            else:
                # Modo desktop/móvil: guardar en archivo JSON
                docs_dir = Path.home() / "Documents" / "NPICMemoryDates"
                docs_dir.mkdir(parents=True, exist_ok=True)
                json_file = docs_dir / "npic_data.json"
                
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error guardando datos: {e}")
            return False
    
    def _initialize_default_data(self):
        """Inicializa datos por defecto con tipos de servicios."""
        tipos_basicos = [
            {"id": 1, "codigo": "carne", "nombre_mostrar": "🥩 Murales Carne", "seccion": "positivo"},
            {"id": 2, "codigo": "pescado", "nombre_mostrar": "🐟 Murales Pescado", "seccion": "positivo"},
            {"id": 3, "codigo": "verdura", "nombre_mostrar": "🥦 Murales Verdura", "seccion": "positivo"},
            {"id": 4, "codigo": "lacteos", "nombre_mostrar": "🥛 Murales Lácteos", "seccion": "positivo"},
            {"id": 5, "codigo": "charcuteria", "nombre_mostrar": "🥓 Murales Charcutería", "seccion": "positivo"},
            {"id": 6, "codigo": "bebidas_frias", "nombre_mostrar": "🥤 Bebidas frías", "seccion": "positivo"},
            {"id": 7, "codigo": "leche_fresca", "nombre_mostrar": "🥛 Leche fresca", "seccion": "positivo"},
            {"id": 8, "codigo": "zumos", "nombre_mostrar": "🧃 Zumos", "seccion": "positivo"},
            {"id": 9, "codigo": "platos_preparados", "nombre_mostrar": "🍽️ Platos preparados", "seccion": "positivo"},
            {"id": 10, "codigo": "vitrina_lpc_ls", "nombre_mostrar": "🥗 Vitrina LPC libre servicio", "seccion": "positivo"},
            {"id": 11, "codigo": "mostrador_lpc", "nombre_mostrar": "🍱 Mostrador LPC", "seccion": "positivo"},
            {"id": 12, "codigo": "murales_lpc", "nombre_mostrar": "🥗 Murales listos para comer", "seccion": "positivo"},
            {"id": 13, "codigo": "mural_sushi", "nombre_mostrar": "🍣 Mural Sushi", "seccion": "positivo"},
            {"id": 14, "codigo": "mural_ensaladas", "nombre_mostrar": "🥗 Mural Ensaladas", "seccion": "positivo"},
            {"id": 15, "codigo": "camaras_refrigerado", "nombre_mostrar": "🚪 Cámaras de refrigerado", "seccion": "positivo"},
            {"id": 16, "codigo": "central_frigorifica_positiva", "nombre_mostrar": "Central frigorífica positiva", "seccion": "positivo"},
            {"id": 17, "codigo": "aacc_lt_12", "nombre_mostrar": "AACC < 12 kW", "seccion": "aacc"},
            {"id": 18, "codigo": "aacc_gt_12", "nombre_mostrar": "AACC ≥ 12 kW", "seccion": "aacc"},
            {"id": 19, "codigo": "murales_vitrinas_calientes", "nombre_mostrar": "Murales y vitrinas calientes", "seccion": "caliente"},
            {"id": 20, "codigo": "fosas_septicas", "nombre_mostrar": "Fosas sépticas", "seccion": "fosas"},
            {"id": 21, "codigo": "isla_carne", "nombre_mostrar": "🥩 Isla Carne Congelada", "seccion": "negativo"},
            {"id": 22, "codigo": "isla_verdura", "nombre_mostrar": "🥦 Isla Verdura Congelada", "seccion": "negativo"},
            {"id": 23, "codigo": "armario_verdura", "nombre_mostrar": "🗄️ Armario Verdura", "seccion": "negativo"},
            {"id": 24, "codigo": "isla_pescado", "nombre_mostrar": "🐟 Isla Pescado Congelado", "seccion": "negativo"},
            {"id": 25, "codigo": "isla_helados", "nombre_mostrar": "🍨 Islas Helados", "seccion": "negativo"},
            {"id": 26, "codigo": "armario_pescado_congelado", "nombre_mostrar": "🐟 Armarios Pescado Congelado", "seccion": "negativo"},
            {"id": 27, "codigo": "isla_marisco", "nombre_mostrar": "🦐 Isla de Marisco", "seccion": "negativo"},
            {"id": 28, "codigo": "isla_tartas", "nombre_mostrar": "🍰 Isla de Tartas", "seccion": "negativo"},
            {"id": 29, "codigo": "camaras_congelado", "nombre_mostrar": "🚪 Cámaras de congelado", "seccion": "negativo"},
            {"id": 30, "codigo": "central_frigorifica_negativa", "nombre_mostrar": "Central frigorífica negativa", "seccion": "negativo"},
        ]
        
        self.data = {
            "equipos": [],
            "mantenimientos": [],
            "tipos": tipos_basicos,
        }
        self.save()
    
    # Métodos de acceso a datos (simulan queries SQL)
    def get_equipos_por_tipo(self, tipo: str) -> Dict[str, Dict]:
        """Obtiene equipos de un tipo específico."""
        equipos = {}
        for eq in self.data["equipos"]:
            if eq.get("tipo") == tipo:
                # Obtener último mantenimiento
                mantenimientos = [m for m in self.data["mantenimientos"] if m["equipo_id"] == eq["id"]]
                ultimo_mant = mantenimientos[-1] if mantenimientos else None
                
                equipos[eq["nombre"]] = {
                    "seccion": eq["seccion"],
                    "date": ultimo_mant["ultima_fecha"] if ultimo_mant else None,
                    "freq": ultimo_mant["frecuencia_dias"] if ultimo_mant else None,
                    "posicion": eq.get("posicion", 0),
                    "nota": eq.get("nota", ""),
                }
        return equipos
    
    def get_equipo_data(self, nombre: str) -> Optional[Dict]:
        """Obtiene datos de un equipo específico."""
        for eq in self.data["equipos"]:
            if eq["nombre"] == nombre:
                mantenimientos = [m for m in self.data["mantenimientos"] if m["equipo_id"] == eq["id"]]
                ultimo_mant = mantenimientos[-1] if mantenimientos else None
                
                return {
                    "nombre": eq["nombre"],
                    "seccion": eq["seccion"],
                    "date": ultimo_mant["ultima_fecha"] if ultimo_mant else None,
                    "freq": ultimo_mant["frecuencia_dias"] if ultimo_mant else None,
                }
        return None
    
    def save_equipo(self, nombre: str, seccion: str, tipo: str = "", posicion: int = 0) -> bool:
        """Guarda o actualiza un equipo."""
        try:
            # Buscar si existe
            for eq in self.data["equipos"]:
                if eq["nombre"] == nombre:
                    eq["seccion"] = seccion
                    eq["tipo"] = tipo
                    eq["posicion"] = posicion
                    self.save()
                    return True
            
            # Si no existe, crear nuevo
            nuevo_id = max([e.get("id", 0) for e in self.data["equipos"]], default=0) + 1
            self.data["equipos"].append({
                "id": nuevo_id,
                "nombre": nombre,
                "seccion": seccion,
                "tipo": tipo,
                "posicion": posicion,
                "nota": "",
            })
            self.save()
            return True
        except Exception as e:
            print(f"Error guardando equipo: {e}")
            return False
    
    def save_mantenimiento(self, equipo_nombre: str, ultima_fecha: str, frecuencia_dias: int) -> bool:
        """Guarda un nuevo mantenimiento."""
        try:
            # Buscar el equipo
            equipo = None
            for eq in self.data["equipos"]:
                if eq["nombre"] == equipo_nombre:
                    equipo = eq
                    break
            
            if not equipo:
                return False
            
            # Agregar nuevo mantenimiento
            nuevo_id = max([m.get("id", 0) for m in self.data["mantenimientos"]], default=0) + 1
            self.data["mantenimientos"].append({
                "id": nuevo_id,
                "equipo_id": equipo["id"],
                "ultima_fecha": ultima_fecha,
                "frecuencia_dias": frecuencia_dias,
            })
            self.save()
            return True
        except Exception as e:
            print(f"Error guardando mantenimiento: {e}")
            return False
    
    def delete_equipo(self, nombre: str) -> bool:
        """Elimina un equipo y sus mantenimientos."""
        try:
            equipo = None
            for eq in self.data["equipos"]:
                if eq["nombre"] == nombre:
                    equipo = eq
                    break
            
            if equipo:
                equipo_id = equipo["id"]
                # Eliminar mantenimientos
                self.data["mantenimientos"] = [m for m in self.data["mantenimientos"] if m["equipo_id"] != equipo_id]
                # Eliminar equipo
                self.data["equipos"] = [e for e in self.data["equipos"] if e["id"] != equipo_id]
                self.save()
            return True
        except Exception as e:
            print(f"Error eliminando equipo: {e}")
            return False
    
    def reset_mantenimiento(self, equipo_nombre: str) -> bool:
        """Elimina los mantenimientos de un equipo."""
        try:
            equipo = None
            for eq in self.data["equipos"]:
                if eq["nombre"] == equipo_nombre:
                    equipo = eq
                    break
            
            if equipo:
                equipo_id = equipo["id"]
                self.data["mantenimientos"] = [m for m in self.data["mantenimientos"] if m["equipo_id"] != equipo_id]
                self.save()
            return True
        except Exception as e:
            print(f"Error reseteando mantenimiento: {e}")
            return False
    
    def get_nota_equipo(self, equipo_nombre: str) -> str:
        """Obtiene la nota de un equipo."""
        for eq in self.data["equipos"]:
            if eq["nombre"] == equipo_nombre:
                return eq.get("nota", "")
        return ""
    
    def set_nota_equipo(self, equipo_nombre: str, nota: str) -> bool:
        """Actualiza la nota de un equipo."""
        try:
            for eq in self.data["equipos"]:
                if eq["nombre"] == equipo_nombre:
                    eq["nota"] = str(nota)[:50]
                    self.save()
                    return True
            return False
        except Exception:
            return False
    
    def rename_equipo(self, old_name: str, new_name: str) -> tuple:
        """Renombra un equipo."""
        try:
            if not new_name or len(new_name.strip()) == 0:
                return False, "El nombre no puede estar vacío"
            
            new_name = new_name.strip()
            
            # Verificar que no exista ya
            for eq in self.data["equipos"]:
                if eq["nombre"] == new_name and new_name != old_name:
                    return False, "Ya existe un equipo con ese nombre"
            
            # Renombrar
            for eq in self.data["equipos"]:
                if eq["nombre"] == old_name:
                    eq["nombre"] = new_name
                    self.save()
                    return True, "Renombrado correctamente"
            
            return False, "Equipo no encontrado"
        except Exception as e:
            return False, str(e)
    
    def change_equipo_position(self, nombre: str, direccion: str) -> bool:
        """Cambia la posición de un equipo."""
        try:
            equipo = None
            tipo = None
            posicion_actual = 0
            
            for eq in self.data["equipos"]:
                if eq["nombre"] == nombre:
                    equipo = eq
                    tipo = eq.get("tipo", "")
                    posicion_actual = eq.get("posicion", 0)
                    break
            
            if not equipo:
                return False
            
            if direccion == "arriba" and posicion_actual > 0:
                # Buscar equipo en posición anterior
                for eq in self.data["equipos"]:
                    if eq.get("tipo") == tipo and eq.get("posicion") == posicion_actual - 1:
                        eq["posicion"] = posicion_actual
                        equipo["posicion"] = posicion_actual - 1
                        self.save()
                        return True
            
            elif direccion == "abajo":
                # Buscar equipo en posición siguiente
                for eq in self.data["equipos"]:
                    if eq.get("tipo") == tipo and eq.get("posicion") == posicion_actual + 1:
                        eq["posicion"] = posicion_actual
                        equipo["posicion"] = posicion_actual + 1
                        self.save()
                        return True
            
            return False
        except Exception as e:
            print(f"Error cambiando posición: {e}")
            return False
    
    def insert_equipo_at_position(self, tipo: str, nombre: str, seccion: str, posicion_deseada: int) -> bool:
        """Inserta un equipo en una posición específica."""
        try:
            # Verificar que no exista ya
            for eq in self.data["equipos"]:
                if eq["nombre"] == nombre:
                    return False
            
            # Contar equipos del tipo
            equipos_tipo = [e for e in self.data["equipos"] if e.get("tipo") == tipo]
            if len(equipos_tipo) >= 10:
                return False
            
            # Ajustar posición
            if posicion_deseada < 0:
                posicion_deseada = 0
            if posicion_deseada > len(equipos_tipo):
                posicion_deseada = len(equipos_tipo)
            
            # Desplazar equipos
            for eq in self.data["equipos"]:
                if eq.get("tipo") == tipo and eq.get("posicion", 0) >= posicion_deseada:
                    eq["posicion"] = eq.get("posicion", 0) + 1
            
            # Insertar nuevo
            nuevo_id = max([e.get("id", 0) for e in self.data["equipos"]], default=0) + 1
            self.data["equipos"].append({
                "id": nuevo_id,
                "nombre": nombre,
                "seccion": seccion,
                "tipo": tipo,
                "posicion": posicion_deseada,
                "nota": "",
            })
            self.save()
            return True
        except Exception as e:
            print(f"Error insertando equipo: {e}")
            return False
    
    def get_tipos_por_seccion(self, seccion: str) -> List[tuple]:
        """Obtiene tipos de una sección."""
        return [(t["codigo"], t["nombre_mostrar"]) for t in self.data["tipos"] if t["seccion"] == seccion]
    
    def get_todos_los_tipos(self) -> List[tuple]:
        """Obtiene todos los tipos."""
        return [(t["codigo"], t["nombre_mostrar"], t["seccion"]) for t in self.data["tipos"]]
    
    def buscar_equipos(self, query: str) -> List[Dict]:
        """Busca equipos por nombre."""
        if not query:
            return []
        
        def limpiar_texto(texto):
            if texto is None:
                return ""
            normalized = unicodedata.normalize("NFD", str(texto))
            sin_tildes = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
            return sin_tildes.lower()
        
        normalized = limpiar_texto(query.strip())
        if not normalized:
            return []
        
        resultados = []
        for eq in self.data["equipos"]:
            nombre_limpio = limpiar_texto(eq["nombre"])
            puntuacion = 0
            
            if normalized == nombre_limpio:
                puntuacion = 1000
            elif nombre_limpio.startswith(normalized):
                puntuacion = 500
            elif f"_{normalized}_" in nombre_limpio or f"_{normalized}" in nombre_limpio or nombre_limpio.startswith(f"{normalized}_"):
                puntuacion = 400
            elif normalized in nombre_limpio:
                puntuacion = 300
            else:
                partes = nombre_limpio.replace("-", "_").split("_")
                for parte in partes:
                    if normalized in parte:
                        if parte.startswith(normalized):
                            puntuacion = max(puntuacion, 200)
                        else:
                            puntuacion = max(puntuacion, 100)
            
            if puntuacion > 0:
                resultados.append({
                    "nombre": eq["nombre"],
                    "seccion": eq["seccion"],
                    "tipo": eq.get("tipo", ""),
                    "puntuacion": puntuacion,
                })
        
        resultados.sort(key=lambda x: x["puntuacion"], reverse=True)
        return [{"nombre": r["nombre"], "seccion": r["seccion"], "tipo": r["tipo"]} for r in resultados[:25]]
    
    def obtener_historial_filtrado(self, fecha_desde=None, fecha_hasta=None, servicios=None):
        """Obtiene historial filtrado."""
        hace_24_meses = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        
        historial = {}
        total = 0
        
        for eq in self.data["equipos"]:
            if servicios and eq.get("tipo") not in servicios:
                continue
            
            for mant in self.data["mantenimientos"]:
                if mant["equipo_id"] != eq["id"]:
                    continue
                
                fecha_valor = mant.get("ultima_fecha")
                if not fecha_valor or fecha_valor < hace_24_meses:
                    continue
                
                try:
                    fecha_dt = datetime.strptime(fecha_valor, "%Y-%m-%d")
                except:
                    continue
                
                if fecha_desde:
                    desde_dt = datetime.strptime(fecha_desde, "%Y-%m-%d")
                    if fecha_dt < desde_dt:
                        continue
                
                if fecha_hasta:
                    hasta_dt = datetime.strptime(fecha_hasta, "%Y-%m-%d")
                    if fecha_dt > hasta_dt:
                        continue
                
                total += 1
                fecha_legible = fecha_dt.strftime("%d/%m/%Y")
                historial.setdefault(eq["nombre"], []).append((fecha_dt, fecha_legible))
        
        # Ordenar fechas
        for nombre in historial:
            historial[nombre].sort(key=lambda item: item[0], reverse=True)
            historial[nombre] = [texto for _, texto in historial[nombre]]
        
        return historial, total
    
    def borrar_historial_entre_fechas(self, fecha_desde: str, fecha_hasta: str) -> int:
        """Elimina mantenimientos entre fechas."""
        try:
            inicial = len(self.data["mantenimientos"])
            self.data["mantenimientos"] = [
                m for m in self.data["mantenimientos"]
                if not (m.get("ultima_fecha", "") >= fecha_desde and m.get("ultima_fecha", "") <= fecha_hasta)
            ]
            borrados = inicial - len(self.data["mantenimientos"])
            if borrados > 0:
                self.save()
            return borrados
        except:
            return 0
    
    def get_all_equipos(self) -> List[tuple]:
        """Obtiene todos los equipos."""
        return [(e["nombre"], e["seccion"], e.get("tipo", ""), e.get("posicion", 0)) for e in self.data["equipos"]]
    
    def exportar_datos_json(self) -> str:
        """Exporta todos los datos como JSON string para backup."""
        return json.dumps(self.data, ensure_ascii=False, indent=2)
    
    def importar_datos_json(self, json_str: str) -> bool:
        """Importa datos desde JSON string."""
        try:
            self.data = json.loads(json_str)
            self.save()
            return True
        except:
            return False

def main(page: ft.Page):
    is_web = page.web if hasattr(page, "web") else False

    page.title = "NPIC Memory Dates"
    if not is_web:
        page.window_width = 900
        page.window_height = 700
        page.window_min_width = 300
        page.window_min_height = 500
    page.padding = 12
    page.bgcolor = "#121821"
    page.scroll = ft.ScrollMode.ALWAYS
    page.locale_configuration = ft.LocaleConfiguration(
        current_locale=ft.Locale("es", "ES"),
        supported_locales=[ft.Locale("es", "ES"), ft.Locale("en", "US")],
    )
    
    # Inicializar servicio de almacenamiento
    storage = StorageService(page)
    try:
        storage.load()
    except Exception as e:
        print(f"Error cargando storage: {e}")
        storage._initialize_default_data()
    
    # Detectar plataforma
    is_web = storage.is_web

    def get_page_width():
        if not is_web:
            return getattr(page, "window_width", None)
        return getattr(page, "width", None)

    def is_narrow_screen():
        width = get_page_width()
        return width is not None and width < 600

    is_mobile = is_narrow_screen()
    
    # Colores (se podrán cambiar con el modo claro/oscuro)
    CARD = "#1B2430"
    ACCENT = "#4FC3F7"
    TEXT = "#FFFFFF"
    SUBTEXT = "#9AA7B2"
    RED = "#E57373"
    ORANGE = "#FFB74D"
    GREEN = "#81C784"
    BLUE = "#64B5F6"

    # Estado de tema
    is_dark_mode = True

    def apply_theme():
        nonlocal CARD, ACCENT, TEXT, SUBTEXT, RED, ORANGE, GREEN, BLUE, is_dark_mode

        if is_dark_mode:
            # Tema oscuro
            CARD = "#1B2430"
            ACCENT = "#4FC3F7"
            TEXT = "#FFFFFF"
            SUBTEXT = "#9AA7B2"
            RED = "#E57373"
            ORANGE = "#FFB74D"
            GREEN = "#81C784"
            BLUE = "#64B5F6"
            page.bgcolor = "#121821"
        else:
            # Tema claro (más suave y luminoso)
            CARD = "#FAFAFA"
            ACCENT = "#039BE5"   # azul claro
            TEXT = "#212121"
            SUBTEXT = "#757575"
            RED = "#E57373"
            ORANGE = "#FFB74D"
            GREEN = "#66BB6A"
            BLUE = "#42A5F5"
            page.bgcolor = "#ECEFF1"

    def cambiar_tema(es_oscuro: bool):
        nonlocal is_dark_mode
        is_dark_mode = es_oscuro
        apply_theme()
        # Volvemos a Acerca de para que se vea el cambio
        show_view(show_about)
    
    DIAS_ALERTA = 10
    
    # Funciones helper que ahora usan StorageService
    def get_equipo_data(equipo_nombre):
        return storage.get_equipo_data(equipo_nombre)
    
    def get_equipos_por_tipo(tipo):
        return storage.get_equipos_por_tipo(tipo)
    
    def save_equipo(nombre, seccion, tipo=""):
        return storage.save_equipo(nombre, seccion, tipo)
    
    def rename_equipo(old_name, new_name):
        return storage.rename_equipo(old_name, new_name)
    
    def save_mantenimiento(equipo_nombre, ultima_fecha, frecuencia_dias):
        return storage.save_mantenimiento(equipo_nombre, ultima_fecha, frecuencia_dias)
    
    def reset_mantenimiento(equipo_nombre):
        return storage.reset_mantenimiento(equipo_nombre)
    
    def change_equipo_position(nombre, direccion):
        return storage.change_equipo_position(nombre, direccion)
    
    def delete_equipo(nombre):
        return storage.delete_equipo(nombre)
    
    def get_nota_equipo(equipo_nombre):
        return storage.get_nota_equipo(equipo_nombre)
    
    def set_nota_equipo(equipo_nombre, nota):
        return storage.set_nota_equipo(equipo_nombre, nota)
    
    def buscar_equipos(query):
        return storage.buscar_equipos(query)
    
    def get_tipos_por_seccion(seccion):
        return storage.get_tipos_por_seccion(seccion)
    
    def get_todos_los_tipos():
        return storage.get_todos_los_tipos()
    
    def insert_equipo_at_position(tipo, nombre, seccion, posicion_deseada):
        return storage.insert_equipo_at_position(tipo, nombre, seccion, posicion_deseada)
    
    def obtener_historial_filtrado(fecha_desde=None, fecha_hasta=None, servicios=None):
        return storage.obtener_historial_filtrado(fecha_desde, fecha_hasta, servicios)
    
    def borrar_historial_entre_fechas(fecha_desde, fecha_hasta):
        return storage.borrar_historial_entre_fechas(fecha_desde, fecha_hasta)
    
    def exportar_base_datos():
        """Exporta una copia de los datos (solo en desktop/móvil)."""
        if is_web:
            # En web, descargar como JSON
            try:
                json_data = storage.exportar_datos_json()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"npic_backup_{timestamp}.json"
                
                # Crear un blob y descargarlo (solo funciona en web)
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("✅ Backup creado. Usa el botón de descarga del navegador."),
                    bgcolor=GREEN,
                )
                page.snack_bar.open = True
                page.update()
                return filename
            except Exception as e:
                print(f"Error en exportación web: {e}")
                return None
        else:
            # En desktop/móvil, copiar archivo JSON
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_name = f"npic_backup_{timestamp}.json"
                export_dir = Path.home() / "Documents" / "NPICMemoryDates" / "backups"
                export_dir.mkdir(parents=True, exist_ok=True)
                export_path = export_dir / export_name
                
                # Exportar datos
                json_data = storage.exportar_datos_json()
                with open(export_path, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                
                return str(export_path)
            except Exception as e:
                print(f"Error exportando: {e}")
                return None
    
    def importar_base_datos(archivo_path_o_json):
        """Importa datos desde archivo o JSON string."""
        try:
            if is_web:
                # En web, esperar JSON string directamente
                return storage.importar_datos_json(archivo_path_o_json)
            else:
                # En desktop, leer desde archivo
                with open(archivo_path_o_json, 'r', encoding='utf-8') as f:
                    json_data = f.read()
                return storage.importar_datos_json(json_data)
        except Exception as e:
            print(f"Error importando: {e}")
            return False

    def construir_csv_historial(historial):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["equipo", "fecha"])
        for nombre in sorted(historial.keys()):
            for fecha in historial[nombre]:
                writer.writerow([nombre, fecha])
        return buffer.getvalue().strip()

    def construir_html_historial(historial, fecha_desde=None, fecha_hasta=None):
        """Construye un HTML con el historial de mantenimientos."""
        html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historial de Mantenimientos</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4FC3F7; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>📚 Historial de Mantenimientos</h1>
"""
        if fecha_desde and fecha_hasta:
            html += f"<p><strong>Periodo:</strong> {fecha_desde} a {fecha_hasta}</p>\n"
        else:
            html += "<p><strong>Periodo:</strong> Últimos 24 meses</p>\n"
        
        html += """    <table>
        <thead>
            <tr>
                <th>Equipo</th>
                <th>Fechas</th>
                <th>Total</th>
            </tr>
        </thead>
        <tbody>
"""
        for nombre in sorted(historial.keys()):
            fechas = historial[nombre]
            fecha_texto = ", ".join(fechas)
            html += f"""            <tr>
                <td>{nombre}</td>
                <td>{fecha_texto}</td>
                <td>{len(fechas)}</td>
            </tr>
"""
        html += """        </tbody>
    </table>
</body>
</html>"""
        return html

    def guardar_historial_en_archivo(nombre_archivo, contenido, ruta_destino=None):
        """Guarda el historial en un archivo (solo desktop/móvil)."""
        if is_web:
            return None  # En web no guardamos archivos locales
        
        try:
            if ruta_destino:
                file_path = Path(ruta_destino) / nombre_archivo
            else:
                docs_dir = Path.home() / "Documents" / "NPICMemoryDates" / "historial"
                docs_dir.mkdir(parents=True, exist_ok=True)
                file_path = docs_dir / nombre_archivo
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(contenido)
            
            return str(file_path)
        except Exception as e:
            print(f"Error guardando historial: {e}")
            return None

    def generar_historial_mantenimientos(
        fecha_desde=None,
        fecha_hasta=None,
        servicios=None,
        formato="html",
        guardar=True,
        ruta_destino=None,
    ):
        """Genera un archivo con el historial de mantenimientos por servicio.

        Devuelve (ruta_archivo, contenido, nombre_archivo).
        Si no hay datos, devuelve (None, None, None).
        Opcionalmente filtra por rango de fechas (formato YYYY-MM-DD) y servicios.
        formato: 'html' (por defecto) o 'csv'.
        guardar: guarda automáticamente en disco si es True.
        ruta_destino: ruta personalizada para el guardado automático.
        servicios: lista de códigos de tipos a incluir, o None para todos.
        """
        historial, total_registros = obtener_historial_filtrado(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            servicios=servicios,
        )

        if total_registros == 0:
            return None, None, None

        formato_limpio = (formato or "html").lower()
        if formato_limpio == "csv":
            contenido = construir_csv_historial(historial)
            nombre_archivo = "historial_mantenimientos.csv"
        else:
            contenido = construir_html_historial(historial, fecha_desde, fecha_hasta)
            nombre_archivo = "historial_mantenimientos.html"

        file_path = None
        if guardar:
            file_path = guardar_historial_en_archivo(
                nombre_archivo,
                contenido,
                ruta_destino=ruta_destino,
            )
        return file_path, contenido, nombre_archivo

    def calculate_days(equipo_nombre):
        data = get_equipo_data(equipo_nombre)
        
        if not data or not data.get("date") or not data.get("freq"):
            return None, None
        
        try:
            ultima_fecha = datetime.strptime(data["date"], "%Y-%m-%d")
            frecuencia_dias = int(data["freq"])
            proxima_fecha = ultima_fecha + timedelta(days=frecuencia_dias)
            dias_restantes = (proxima_fecha - datetime.now()).days
            return dias_restantes, proxima_fecha.strftime("%d/%m/%Y")
        except:
            return None, None
    
    # calculate_days ya utiliza get_equipo_data(), que a su vez
    # delega en StorageService. Las búsquedas también se realizan
    # mediante storage.buscar_equipos() definido más arriba.
    
    # Aplicar tema inicial (oscuro por defecto)
    apply_theme()

    # ============ FUNCIONES DE INTERFAZ ============
    def clear_page():
        page.controls.clear()
        # Limpiar FAB al cambiar de vista
        page.floating_action_button = None
    
    def show_view(view_func, *args):
        clear_page()
        view_func(*args)
        page.update()
    
    def create_card(content, on_click=None, bgcolor=CARD, border_color=None):
        if border_color:
            card = ft.Container(
                content=content,
                bgcolor=bgcolor,
                padding=10,
                border_radius=12,
                border=ft.Border.all(3, border_color),
            )
        else:
            card = ft.Container(
                content=content,
                bgcolor=bgcolor,
                padding=10,
                border_radius=12,
                border=ft.Border.all(1, SUBTEXT),
            )
        
        if on_click:
            card.on_click = on_click
            
        return card
    
    def create_button(text, on_click, bgcolor=ACCENT, width=None, height=40):
        return ft.Button(
            content=ft.Text(text, size=14, weight="bold"),
            on_click=on_click,
            bgcolor=bgcolor,
            color=TEXT,
            height=height,
            width=width,
            expand=True if width is None else False,
        )

    def preparar_historial_para_impresion(fecha_desde=None, fecha_hasta=None, servicios=None):
        """Genera un HTML temporal y lo abre en el navegador para permitir imprimir."""
        try:
            _, contenido, _ = generar_historial_mantenimientos(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                servicios=servicios,
                formato="html",
                guardar=False,
            )
        except Exception as exc:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"No se pudo preparar el historial: {exc}"),
                bgcolor=RED,
            )
            page.snack_bar.open = True
            page.update()
            return

        if not contenido:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("No hay datos para imprimir con esos filtros"),
                bgcolor=ORANGE,
            )
            page.snack_bar.open = True
            page.update()
            return

        # En web no podemos crear ficheros temporales locales; mostramos
        # el contenido en una vista imprimible dentro de la propia app.
        if is_web:
            clear_page()
            page.add(
                ft.Column(
                    [
                        ft.Row([
                            create_button("← Volver", lambda e: open_historial_menu(), bgcolor=SUBTEXT, width=120, height=48),
                            ft.Text("Historial listo para imprimir", size=18, weight="bold", color=ACCENT, expand=True),
                        ], spacing=8),
                        ft.Container(height=12),
                        ft.Text("Usa la opción de Imprimir del navegador (Ctrl+P)", size=12, color=SUBTEXT),
                        ft.Container(height=12),
                        ft.Container(
                            content=ft.Text(contenido, selectable=True, size=11, color=TEXT),
                            bgcolor=f"{CARD}80",
                            padding=10,
                            border_radius=8,
                            expand=True,
                        ),
                    ],
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                )
            )
            page.update()
            return

        # Desktop / móvil: crear HTML temporal y abrir en navegador
        try:
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = os.path.join(temp_dir, f"npic_historial_{timestamp}.html")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(contenido)
            if webbrowser is None:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("No se puede abrir el navegador en este entorno"),
                    bgcolor=ORANGE,
                )
                page.snack_bar.open = True
                page.update()
                return
            webbrowser.open(Path(temp_path).as_uri())
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Historial abierto; usa Imprimir en el navegador"),
                bgcolor=GREEN,
                duration=3500,
            )
            page.snack_bar.open = True
            page.update()
        except Exception as exc:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"No se pudo abrir el historial: {exc}"),
                bgcolor=RED,
            )
            page.snack_bar.open = True
            page.update()
    
    # ============ VISTAS ============
    def mostrar_historial(fecha_desde=None, fecha_hasta=None, servicios=None):
        """Muestra el historial filtrado."""
        historial, total_registros = obtener_historial_filtrado(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            servicios=servicios,
        )

        if total_registros == 0:
            mensaje = (
                "No hay mantenimientos registrados con esos filtros"
                if (fecha_desde or fecha_hasta or servicios)
                else "No hay mantenimientos registrados todavía"
            )
            page.snack_bar = ft.SnackBar(
                content=ft.Text(mensaje),
                bgcolor=RED,
            )
            page.snack_bar.open = True
            page.update()
            return

        def volver_historial(e):
            open_historial_menu()
        
        def exportar_historial_actual(e):
            # Guardar las fechas actuales para la exportación
            show_view(show_export_historial_options, fecha_desde, fecha_hasta, servicios)

        # Construir lista de tarjetas
        historial_cards = []
        for nombre in sorted(historial.keys()):
            fechas = historial[nombre]
            fecha_texto = ", ".join(fechas)
            historial_cards.append(
                create_card(
                    ft.Column([
                        ft.Row([
                            ft.Text(nombre, size=13, weight="bold", color=ACCENT, expand=True),
                            ft.Text(f"({len(fechas)})", size=11, color=SUBTEXT),
                        ], spacing=4),
                        ft.Text(f"📅 {fecha_texto}", size=11, color=TEXT),
                    ], spacing=3),
                    border_color=ACCENT,
                )
            )

        # Vista completa
        vista_historial = ft.Column(
            [
                ft.Row([
                    create_button("← Volver", volver_historial, bgcolor=SUBTEXT, height=48, width=120),
                    ft.Container(expand=True),
                    create_button("💾 Exportar", exportar_historial_actual, bgcolor=GREEN, height=48, width=120),
                ], spacing=8),
                ft.Container(height=8),
                ft.Text("📚 Historial de mantenimientos", size=18, weight="bold", color=ACCENT),
                ft.Text(
                    f"{total_registros} registros"
                    + (f" ({fecha_desde} a {fecha_hasta})" if fecha_desde and fecha_hasta else " (Últimos 24 meses)"),
                    size=12,
                    color=SUBTEXT,
                ),
                ft.Container(height=12),
                ft.Column(
                    controls=historial_cards,
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

        clear_page()
        page.add(vista_historial)
        page.update()

    def open_delete_history_dialog():
        """Diálogo para borrar historial entre dos fechas (solo mantenimientos)."""

        fecha_desde_field = ft.TextField(
            label="Desde (YYYY-MM-DD)",
            width=220,
            height=45,
            border_color=ACCENT,
        )
        fecha_hasta_field = ft.TextField(
            label="Hasta (YYYY-MM-DD)",
            width=220,
            height=45,
            border_color=ACCENT,
        )

        date_picker_desde = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
        )
        date_picker_hasta = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
        )

        def on_date_desde_change(e):
            try:
                if date_picker_desde.value:
                    v = date_picker_desde.value
                    if isinstance(v, str):
                        fecha_desde_field.value = v
                    else:
                        fecha_desde_field.value = v.strftime("%Y-%m-%d")
                    fecha_desde_field.update()
            except Exception:
                pass

        def on_date_hasta_change(e):
            try:
                if date_picker_hasta.value:
                    v = date_picker_hasta.value
                    if isinstance(v, str):
                        fecha_hasta_field.value = v
                    else:
                        fecha_hasta_field.value = v.strftime("%Y-%m-%d")
                    fecha_hasta_field.update()
            except Exception:
                pass

        date_picker_desde.on_change = on_date_desde_change
        date_picker_hasta.on_change = on_date_hasta_change

        if date_picker_desde not in page.overlay:
            page.overlay.append(date_picker_desde)
        if date_picker_hasta not in page.overlay:
            page.overlay.append(date_picker_hasta)

        mensaje_text = ft.Text("", size=12)

        def borrar(e):
            f_desde = (fecha_desde_field.value or "").strip()
            f_hasta = (fecha_hasta_field.value or "").strip()

            if not f_desde or not f_hasta:
                mensaje_text.value = "Rellena ambas fechas"
                mensaje_text.color = ORANGE
                mensaje_text.update()
                return

            try:
                d1 = datetime.strptime(f_desde, "%Y-%m-%d")
                d2 = datetime.strptime(f_hasta, "%Y-%m-%d")
            except ValueError:
                mensaje_text.value = "Formato de fecha incorrecto (usa YYYY-MM-DD)"
                mensaje_text.color = RED
                mensaje_text.update()
                return

            if d1 > d2:
                mensaje_text.value = "La fecha 'Desde' no puede ser mayor que 'Hasta'"
                mensaje_text.color = ORANGE
                mensaje_text.update()
                return

            # Mostrar diálogo de confirmación
            def confirmar_borrado(e_confirm):
                borrados = borrar_historial_entre_fechas(f_desde, f_hasta)

                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Se han borrado {borrados} registros de historial"),
                    bgcolor=GREEN if borrados > 0 else SUBTEXT,
                )
                page.snack_bar.open = True
                dialog_confirm.open = False
                page.update()

                # Volver a la pantalla principal
                show_view(show_home)
            
            def cancelar_borrado(e_cancel):
                dialog_confirm.open = False
                page.update()
            
            dialog_confirm = ft.AlertDialog(
                modal=True,
                title=ft.Text("⚠️ ¿Estás seguro?", color=ORANGE),
                content=ft.Text(
                    f"Esta acción borrará PERMANENTEMENTE todos los registros de historial entre {f_desde} y {f_hasta}.\n\nEsta operación es IRREVERSIBLE.",
                    size=13,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancelar_borrado),
                    ft.TextButton(
                        "Sí, borrar",
                        on_click=confirmar_borrado,
                        style=ft.ButtonStyle(color=ft.colors.RED),
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.dialog = dialog_confirm
            dialog_confirm.open = True
            page.update()

        def cancelar(e):
            show_view(show_home)

        fecha_desde_row = ft.Row([
            fecha_desde_field,
            ft.Container(
                content=ft.Text("📅", size=20),
                on_click=lambda e: setattr(date_picker_desde, "open", True) or page.update(),
                padding=10,
                border_radius=8,
                bgcolor=f"{ACCENT}20",
                tooltip="Seleccionar fecha de inicio",
            ),
        ])

        fecha_hasta_row = ft.Row([
            fecha_hasta_field,
            ft.Container(
                content=ft.Text("📅", size=20),
                on_click=lambda e: setattr(date_picker_hasta, "open", True) or page.update(),
                padding=10,
                border_radius=8,
                bgcolor=f"{ACCENT}20",
                tooltip="Seleccionar fecha final",
            ),
        ])

        dialog_content = ft.Column([
            ft.Text("🧹 Borrar historial", size=18, weight="bold", color=ACCENT),
            ft.Container(height=10),
            ft.Text("Solo se eliminan registros de historial de mantenimientos.", size=12, color=SUBTEXT),
            ft.Text("Los servicios, notas y configuración se mantienen.", size=12, color=SUBTEXT),
            ft.Container(height=15),
            fecha_desde_row,
            ft.Container(height=10),
            fecha_hasta_row,
            ft.Container(height=12),
            mensaje_text,
            ft.Container(height=20),
            ft.Row([
                create_button("Cancelar", cancelar, bgcolor=SUBTEXT, width=120),
                create_button("Borrar", borrar, bgcolor=RED, width=120),
            ], alignment="center"),
        ], spacing=4)

        clear_page()
        page.add(
            ft.Column(
                [
                    ft.Container(
                        content=dialog_content,
                        bgcolor=CARD,
                        padding=25,
                        border_radius=15,
                        border=ft.Border.all(3, RED),
                        width=520,
                    )
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        page.update()
    
    def open_search_history_dialog():
        """Diálogo para buscar historial entre dos fechas."""
        
        # Valores por defecto: últimos 24 meses
        hoy = datetime.now()
        hace_24_meses = hoy - timedelta(days=730)
        
        fecha_desde_field = ft.TextField(
            label="Desde (YYYY-MM-DD)",
            value=hace_24_meses.strftime("%Y-%m-%d"),
            width=220,
            height=45,
            border_color=ACCENT,
        )
        fecha_hasta_field = ft.TextField(
            label="Hasta (YYYY-MM-DD)",
            value=hoy.strftime("%Y-%m-%d"),
            width=220,
            height=45,
            border_color=ACCENT,
        )

        date_picker_desde = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
        )
        date_picker_hasta = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
        )

        def on_date_desde_change(e):
            try:
                if date_picker_desde.value:
                    v = date_picker_desde.value
                    if isinstance(v, str):
                        fecha_desde_field.value = v
                    else:
                        fecha_desde_field.value = v.strftime("%Y-%m-%d")
                    fecha_desde_field.update()
            except Exception:
                pass

        def on_date_hasta_change(e):
            try:
                if date_picker_hasta.value:
                    v = date_picker_hasta.value
                    if isinstance(v, str):
                        fecha_hasta_field.value = v
                    else:
                        fecha_hasta_field.value = v.strftime("%Y-%m-%d")
                    fecha_hasta_field.update()
            except Exception:
                pass

        date_picker_desde.on_change = on_date_desde_change
        date_picker_hasta.on_change = on_date_hasta_change

        if date_picker_desde not in page.overlay:
            page.overlay.append(date_picker_desde)
        if date_picker_hasta not in page.overlay:
            page.overlay.append(date_picker_hasta)

        mensaje_text = ft.Text("", size=12)

        def buscar_y_ver(e):
            desde = (fecha_desde_field.value or "").strip()
            hasta = (fecha_hasta_field.value or "").strip()

            if not desde or not hasta:
                mensaje_text.value = "⚠️ Completa ambas fechas"
                mensaje_text.color = ORANGE
                mensaje_text.update()
                return

            try:
                d1 = datetime.strptime(desde, "%Y-%m-%d")
                d2 = datetime.strptime(hasta, "%Y-%m-%d")
            except ValueError:
                mensaje_text.value = "❌ Formato debe ser YYYY-MM-DD"
                mensaje_text.color = RED
                mensaje_text.update()
                return

            if d1 > d2:
                mensaje_text.value = "⚠️ La fecha inicial debe ser anterior a la final"
                mensaje_text.color = ORANGE
                mensaje_text.update()
                return

            _, total = obtener_historial_filtrado(fecha_desde=desde, fecha_hasta=hasta)
            
            if total == 0:
                mensaje_text.value = f"ℹ️ No hay registros entre {desde} y {hasta}"
                mensaje_text.color = SUBTEXT
                mensaje_text.update()
                return
            
            mostrar_historial(desde, hasta)

        def cancelar(e):
            open_historial_menu()

        fecha_desde_row = ft.Row([
            fecha_desde_field,
            ft.Container(
                content=ft.Text("📅", size=16),
                on_click=lambda e: setattr(date_picker_desde, "open", True) or page.update(),
                padding=6,
                border_radius=8,
                bgcolor=f"{ACCENT}20",
                width=45,
                height=45,
                tooltip="Calendario",
            ),
        ], spacing=8)

        fecha_hasta_row = ft.Row([
            fecha_hasta_field,
            ft.Container(
                content=ft.Text("📅", size=16),
                on_click=lambda e: setattr(date_picker_hasta, "open", True) or page.update(),
                padding=6,
                border_radius=8,
                bgcolor=f"{ACCENT}20",
                width=45,
                height=45,
                tooltip="Calendario",
            ),
        ], spacing=8)

        dialog_content = ft.Column([
            ft.Text("🔍 Buscar historial por fechas", size=17, weight="bold", color=ACCENT),
            ft.Container(height=15),
            fecha_desde_row,
            ft.Container(height=10),
            fecha_hasta_row,
            ft.Container(height=22),
            mensaje_text,
            ft.Container(height=20),
            create_button("Ver historial", buscar_y_ver, bgcolor=BLUE, height=48),
            ft.Container(height=8),
            create_button("Volver", cancelar, bgcolor=SUBTEXT, height=48),
        ], spacing=4)

        clear_page()
        page.add(
            ft.Column(
                [
                    ft.Container(
                        content=dialog_content,
                        bgcolor=CARD,
                        padding=25,
                        border_radius=15,
                        border=ft.Border.all(3, ACCENT),
                        width=520,
                    )
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        page.update()

    def open_filtro_historial_dialog():
        """Diálogo con filtros de fechas y servicios para ver el historial."""
        # Valores por defecto: vacío (muestra últimos 24 meses)
        hoy = datetime.now()
        hace_un_mes = hoy - timedelta(days=30)
        
        fecha_desde_field = ft.TextField(
            label="Desde (opcional)",
            hint_text="YYYY-MM-DD",
            width=200,
            height=45,
            border_color=ACCENT,
        )
        fecha_hasta_field = ft.TextField(
            label="Hasta (opcional)",
            hint_text="YYYY-MM-DD",
            width=200,
            height=45,
            border_color=ACCENT,
        )

        date_picker_desde = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
        )
        date_picker_hasta = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
        )

        def on_date_desde_change(e):
            try:
                if date_picker_desde.value:
                    v = date_picker_desde.value
                    if isinstance(v, str):
                        fecha_desde_field.value = v
                    else:
                        fecha_desde_field.value = v.strftime("%Y-%m-%d")
                    fecha_desde_field.update()
            except Exception:
                pass

        def on_date_hasta_change(e):
            try:
                if date_picker_hasta.value:
                    v = date_picker_hasta.value
                    if isinstance(v, str):
                        fecha_hasta_field.value = v
                    else:
                        fecha_hasta_field.value = v.strftime("%Y-%m-%d")
                    fecha_hasta_field.update()
            except Exception:
                pass

        date_picker_desde.on_change = on_date_desde_change
        date_picker_hasta.on_change = on_date_hasta_change

        # Obtener todos los servicios agrupados por sección
        todos_tipos = get_todos_los_tipos()
        
        # Agrupar por sección
        servicios_por_seccion = {}
        for codigo, nombre, seccion in todos_tipos:
            if seccion not in servicios_por_seccion:
                servicios_por_seccion[seccion] = []
            servicios_por_seccion[seccion].append((codigo, nombre))
        
        # Checkboxes para servicios
        servicios_seleccionados = {}
        servicios_checkboxes = []
        
        # Checkbox "Todos"
        todos_checkbox = ft.Checkbox(
            label="Todos los servicios",
            value=True,
            fill_color=ACCENT,
        )
        
        def on_todos_change(e):
            seleccionar_todo = todos_checkbox.value
            for cb in servicios_checkboxes:
                cb.value = seleccionar_todo
                cb.update()
        
        todos_checkbox.on_change = on_todos_change
        
        for seccion_nombre in ["positivo", "negativo", "aacc", "caliente", "fosas"]:
            if seccion_nombre in servicios_por_seccion:
                for codigo, nombre in servicios_por_seccion[seccion_nombre]:
                    cb = ft.Checkbox(
                        label=nombre,
                        value=True,
                        fill_color=ACCENT,
                    )
                    servicios_seleccionados[codigo] = cb
                    servicios_checkboxes.append(cb)
        
        servicios_column = ft.Column(
            [todos_checkbox] + servicios_checkboxes,
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            height=200,
        )

        mensaje_text = ft.Text("", size=12)

        def ejecutar_accion(e):
            desde = (fecha_desde_field.value or "").strip()
            hasta = (fecha_hasta_field.value or "").strip()
            
            # Validar fechas si se proporcionan
            if desde or hasta:
                if not desde or not hasta:
                    mensaje_text.value = "⚠️ Proporciona ambas fechas o deja ambas vacías"
                    mensaje_text.color = ORANGE
                    mensaje_text.update()
                    return
                
                try:
                    d1 = datetime.strptime(desde, "%Y-%m-%d")
                    d2 = datetime.strptime(hasta, "%Y-%m-%d")
                except ValueError:
                    mensaje_text.value = "❌ Formato debe ser YYYY-MM-DD"
                    mensaje_text.color = RED
                    mensaje_text.update()
                    return

                if d1 > d2:
                    mensaje_text.value = "⚠️ La fecha inicial debe ser anterior a la final"
                    mensaje_text.color = ORANGE
                    mensaje_text.update()
                    return
            
            # Obtener servicios seleccionados
            if todos_checkbox.value:
                servicios = None  # Todos
            else:
                servicios = [codigo for codigo, cb in servicios_seleccionados.items() if cb.value]
                if not servicios:
                    mensaje_text.value = "⚠️ Selecciona al menos un servicio"
                    mensaje_text.color = ORANGE
                    mensaje_text.update()
                    return
            
            mostrar_historial(
                fecha_desde=desde if desde else None,
                fecha_hasta=hasta if hasta else None,
                servicios=servicios,
            )

        def cancelar(e):
            show_view(open_historial_menu)

        titulo = "📊 Ver historial"
        boton_texto = "Ver historial"
        boton_color = BLUE

        dialog_content = ft.Column([
            ft.Text(titulo, size=17, weight="bold", color=ACCENT),
            ft.Container(height=10),
            ft.Text("Filtros opcionales:", size=13, color=SUBTEXT),
            ft.Container(height=8),
            ft.Row([
                fecha_desde_field,
                ft.Container(
                    content=ft.Text("📅", size=16),
                    on_click=lambda e: setattr(date_picker_desde, "open", True) or page.update(),
                    padding=6,
                    border_radius=8,
                    bgcolor=f"{ACCENT}20",
                    width=45,
                    height=45,
                    tooltip="Calendario",
                ),
            ], spacing=8),
            ft.Row([
                fecha_hasta_field,
                ft.Container(
                    content=ft.Text("📅", size=16),
                    on_click=lambda e: setattr(date_picker_hasta, "open", True) or page.update(),
                    padding=6,
                    border_radius=8,
                    bgcolor=f"{ACCENT}20",
                    width=45,
                    height=45,
                    tooltip="Calendario",
                ),
            ], spacing=8),
            ft.Container(height=8),
            ft.Container(height=2),
            ft.Text("Servicios:", size=13, color=SUBTEXT),
            ft.Container(
                content=servicios_column,
                bgcolor=f"{CARD}80",
                padding=10,
                border_radius=8,
            ),
            ft.Container(height=8),
            mensaje_text,
            ft.Container(height=20),
            create_button(boton_texto, ejecutar_accion, bgcolor=boton_color, height=48),
            ft.Container(height=6),
            create_button("Volver", cancelar, bgcolor=SUBTEXT, height=48),
        ], spacing=4, scroll=ft.ScrollMode.AUTO)

        clear_page()
        
        # Agregar los DatePickers al overlay
        if date_picker_desde not in page.overlay:
            page.overlay.append(date_picker_desde)
        if date_picker_hasta not in page.overlay:
            page.overlay.append(date_picker_hasta)
        
        page.add(
            ft.Column(
                [
                    ft.Container(
                        content=dialog_content,
                        bgcolor=CARD,
                        padding=20,
                        border_radius=15,
                        border=ft.Border.all(3, ACCENT),
                        width=min(500, get_page_width() - 40) if get_page_width() and get_page_width() > 40 else 500,
                    )
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            )
        )
        page.update()

    def open_historial_menu():
        """Menú para elegir ver, buscar o limpiar el historial."""

        def ver(e):
            open_filtro_historial_dialog()

        def buscar_fechas(e):
            open_search_history_dialog()

        def eliminar(e):
            open_delete_history_dialog()
        
        def exportar_historial(e):
            # Exportar todo el historial (últimos 24 meses)
            show_view(show_export_historial_options, None, None, None)
        
        def exportar_db(e):
            show_view(show_export_options)
        
        def importar_db(e):
            show_view(show_import_backup_list)

        def cancelar(e):
            show_view(show_home)

        dialog_content = ft.Column([
            ft.Text("📚 Historial de mantenimientos", size=17, weight="bold", color=ACCENT),
            ft.Container(height=10),
            ft.Text("Elige qué quieres hacer con el historial.", size=12, color=SUBTEXT),
            ft.Container(height=12),
            create_button("Ver historial", ver, bgcolor=BLUE, height=48),
            ft.Container(height=6),
            create_button("Buscar por fechas", buscar_fechas, bgcolor=GREEN, height=48),
            ft.Container(height=6),
            create_button("📄 Exportar historial", exportar_historial, bgcolor="#9C27B0", height=48),
            ft.Container(height=6),
            create_button("Eliminar (fechas)", eliminar, bgcolor=RED, height=48),
            ft.Container(height=12),
            ft.Text("💾 Backup de datos", size=14, weight="bold", color=ACCENT),
            ft.Container(height=6),
            create_button("💾 Exportar base de datos", exportar_db, bgcolor="#4CAF50", height=48),
            ft.Container(height=6),
            create_button("📥 Importar base de datos", importar_db, bgcolor="#FF9800", height=48),
            ft.Container(height=12),
            create_button("Cerrar", cancelar, bgcolor=SUBTEXT, height=48),
        ], spacing=2)

        clear_page()
        page.add(
            ft.Column(
                [
                    ft.Container(
                        content=dialog_content,
                        bgcolor=CARD,
                        padding=16,
                        border_radius=15,
                        border=ft.Border.all(3, ACCENT),
                        expand=True,
                    )
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        page.update()

    def show_import_backup_list():
        """Muestra lista de backups disponibles para importar."""
        def back_menu(e):
            show_view(show_home)
        
        # Buscar backups en la carpeta
        try:
            backup_dir = Path.home() / "Documents" / "NPICMemoryDates" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Listar archivos .db ordenados por fecha (más recientes primero)
            backups = sorted(
                [f for f in backup_dir.glob("*.db")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
        except Exception:
            backups = []
        
        page.add(
            ft.Row([
                create_button("← Volver", back_menu, bgcolor=SUBTEXT, width=120, height=48),
                ft.Text("📥 Importar backup", size=18, weight="bold", color=ACCENT, expand=True),
            ], spacing=8)
        )
        page.add(ft.Container(height=12))
        
        if not backups:
            page.add(
                create_card(
                    ft.Column([
                        ft.Text("❌", size=48),
                        ft.Text("No hay backups disponibles", size=16, weight="bold", color=SUBTEXT),
                        ft.Text("Primero exporta una copia de seguridad", size=12, color=SUBTEXT),
                    ], horizontal_alignment="center", spacing=8),
                    bgcolor=CARD,
                )
            )
        else:
            page.add(
                ft.Text(f"📂 Carpeta: {backup_dir}", size=10, color=SUBTEXT, selectable=True)
            )
            page.add(ft.Container(height=8))
            
            def importar_backup(ruta_archivo):
                def confirmar(e):
                    if importar_base_datos(str(ruta_archivo)):
                        page.snack_bar = ft.SnackBar(
                            content=ft.Text("✅ Base de datos importada\nReinicia la app para ver los cambios"),
                            bgcolor=GREEN,
                            duration=5000,
                        )
                        page.snack_bar.open = True
                        page.update()
                        # Volver al menú
                        import time
                        time.sleep(1)
                        show_view(show_home)
                    else:
                        page.snack_bar = ft.SnackBar(
                            content=ft.Text("❌ Error al importar"),
                            bgcolor=RED,
                        )
                        page.snack_bar.open = True
                        page.update()
                
                # Mostrar confirmación
                dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("⚠️ Confirmar importación", color=ORANGE),
                    content=ft.Text(
                        f"Se importará el backup:\n{ruta_archivo.name}\n\nSe creará un backup de la base actual antes de importar.\n\n¿Continuar?",
                        size=13,
                    ),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False) or page.update()),
                        ft.TextButton("Sí, importar", on_click=confirmar),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                page.dialog = dialog
                dialog.open = True
                page.update()
            
            # Mostrar lista de backups
            for backup in backups[:10]:  # Máximo 10 backups
                # Fecha de modificación
                fecha_mod = datetime.fromtimestamp(backup.stat().st_mtime)
                fecha_str = fecha_mod.strftime("%d/%m/%Y %H:%M")
                
                # Tamaño del archivo
                tamanyo_kb = backup.stat().st_size / 1024
                tamanyo_str = f"{tamanyo_kb:.1f} KB"
                
                page.add(
                    create_card(
                        ft.Column([
                            ft.Text(backup.name, size=13, weight="bold", color=TEXT),
                            ft.Row([
                                ft.Text(f"📅 {fecha_str}", size=11, color=SUBTEXT),
                                ft.Text(f"💾 {tamanyo_str}", size=11, color=SUBTEXT),
                            ], spacing=12),
                        ], spacing=4),
                        on_click=lambda e, b=backup: importar_backup(b),
                        border_color=ACCENT,
                    )
                )
                page.add(ft.Container(height=6))
    
    def show_export_historial_options(fecha_desde=None, fecha_hasta=None, servicios=None):
        """Muestra opciones para exportar el historial."""
        def back_historial(e):
            mostrar_historial(fecha_desde, fecha_hasta, servicios)
        
        def exportar_html_app(e):
            exportar_con_formato("html", "app", fecha_desde, fecha_hasta, servicios)
        
        def exportar_html_descargas(e):
            exportar_con_formato("html", "descargas", fecha_desde, fecha_hasta, servicios)
        
        def exportar_csv_app(e):
            exportar_con_formato("csv", "app", fecha_desde, fecha_hasta, servicios)
        
        def exportar_csv_descargas(e):
            exportar_con_formato("csv", "descargas", fecha_desde, fecha_hasta, servicios)
        
        def exportar_con_formato(formato, ubicacion, fecha_desde, fecha_hasta, servicios):
            # Mostrar indicador
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"⏳ Exportando historial en {formato.upper()}..."),
                bgcolor=BLUE,
            )
            page.snack_bar.open = True
            page.update()
            
            try:
                # Generar historial sin guardarlo automáticamente
                ruta_archivo, contenido, nombre_archivo = generar_historial_mantenimientos(
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                    servicios=servicios,
                    formato=formato,
                    guardar=False,
                )
                
                if not contenido:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("❌ No hay datos para exportar"),
                        bgcolor=RED,
                        duration=4000,
                    )
                    page.snack_bar.open = True
                    page.update()
                    return
                
                # Guardar según ubicación - Compatible con Android
                if ubicacion == "descargas":
                    # En Android usar /storage/emulated/0/Download
                    try:
                        # Intentar Android primero
                        download_dir = Path("/storage/emulated/0/Download")
                        if not download_dir.exists():
                            # Fallback a Downloads normal
                            download_dir = Path.home() / "Downloads"
                        download_dir.mkdir(parents=True, exist_ok=True)
                        ruta_final = download_dir / nombre_archivo
                    except Exception:
                        # Si falla, usar Documents como último recurso
                        download_dir = Path.home() / "Documents" / "NPICMemoryDates"
                        download_dir.mkdir(parents=True, exist_ok=True)
                        ruta_final = download_dir / nombre_archivo
                else:
                    # Carpeta de la app
                    base_dir = obtener_directorio_historial()
                    ruta_final = os.path.join(base_dir, nombre_archivo)
                
                with open(ruta_final, "w", encoding="utf-8") as f:
                    f.write(contenido)
                
                # Confirmación de éxito con información clara
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ ¡EXPORTADO CON ÉXITO!\n\nFormato: {formato.upper()}\nArchivo: {nombre_archivo}\nUbicación: {ruta_final.parent if hasattr(ruta_final, 'parent') else os.path.dirname(ruta_final)}", size=11),
                    bgcolor=GREEN,
                    duration=10000,
                )
            except Exception as ex:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ Error: {str(ex)}"),
                    bgcolor=RED,
                )
            page.snack_bar.open = True
            page.update()
        
        page.add(
            ft.Row([
                create_button("← Volver", back_historial, bgcolor=SUBTEXT, width=120, height=48),
                ft.Text("💾 Exportar historial", size=18, weight="bold", color=ACCENT, expand=True),
            ], spacing=8)
        )
        page.add(ft.Container(height=12))
        
        page.add(
            ft.Text("Elige formato y ubicación:", size=15, weight="bold", color=TEXT)
        )
        page.add(ft.Container(height=16))
        
        # HTML
        page.add(ft.Text("📄 Formato HTML (para ver/imprimir)", size=14, weight="bold", color=ACCENT))
        page.add(ft.Container(height=8))
        
        page.add(
            ft.Row([
                ft.Container(
                    create_card(
                        ft.Column([
                            ft.Text("📁 Carpeta app", size=14, weight="bold", color=TEXT),
                            ft.Text("Documents/NPICMemoryDates", size=10, color=SUBTEXT),
                        ], spacing=4, horizontal_alignment="center"),
                        on_click=exportar_html_app,
                        border_color=GREEN,
                        bgcolor=f"{GREEN}10",
                    ),
                    expand=1,
                ),
                ft.Container(width=12),
                ft.Container(
                    create_card(
                        ft.Column([
                            ft.Text("📥 Descargas", size=14, weight="bold", color=TEXT),
                            ft.Text("Fácil de encontrar", size=10, color=SUBTEXT),
                        ], spacing=4, horizontal_alignment="center"),
                        on_click=exportar_html_descargas,
                        border_color=BLUE,
                        bgcolor=f"{BLUE}10",
                    ),
                    expand=1,
                ),
            ], spacing=0)
        )
        
        page.add(ft.Container(height=16))
        
        # CSV
        page.add(ft.Text("📊 Formato CSV (para Excel)", size=14, weight="bold", color=ACCENT))
        page.add(ft.Container(height=8))
        
        page.add(
            ft.Row([
                ft.Container(
                    create_card(
                        ft.Column([
                            ft.Text("📁 Carpeta app", size=14, weight="bold", color=TEXT),
                            ft.Text("Documents/NPICMemoryDates", size=10, color=SUBTEXT),
                        ], spacing=4, horizontal_alignment="center"),
                        on_click=exportar_csv_app,
                        border_color=GREEN,
                        bgcolor=f"{GREEN}10",
                    ),
                    expand=1,
                ),
                ft.Container(width=12),
                ft.Container(
                    create_card(
                        ft.Column([
                            ft.Text("📥 Descargas", size=14, weight="bold", color=TEXT),
                            ft.Text("Fácil de encontrar", size=10, color=SUBTEXT),
                        ], spacing=4, horizontal_alignment="center"),
                        on_click=exportar_csv_descargas,
                        border_color=BLUE,
                        bgcolor=f"{BLUE}10",
                    ),
                    expand=1,
                ),
            ], spacing=0)
        )
    
    def show_export_options():
        """Muestra opciones para exportar la base de datos."""
        def back_menu(e):
            show_view(show_home)
        
        def exportar_carpeta_app(e):
            # Mostrar indicador de carga
            page.snack_bar = ft.SnackBar(
                content=ft.Text("⏳ Exportando base de datos..."),
                bgcolor=BLUE,
            )
            page.snack_bar.open = True
            page.update()
            
            ruta = exportar_base_datos()
            if ruta:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ ¡BACKUP EXPORTADO CON ÉXITO!\n\nUbicación:\n{ruta}", size=11),
                    bgcolor=GREEN,
                    duration=10000,
                )
            else:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("❌ Error al exportar la base de datos"),
                    bgcolor=RED,
                    duration=4000,
                )
            page.snack_bar.open = True
            page.update()
        
        def exportar_descargas(e):
            # En web no se puede escribir directamente en el sistema de archivos
            if is_web:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("En la versión Web/PWA usa el backup estándar (se guarda en el navegador)."),
                    bgcolor=ORANGE,
                )
                page.snack_bar.open = True
                page.update()
                return

            # Mostrar indicador de carga
            page.snack_bar = ft.SnackBar(
                content=ft.Text("⏳ Exportando a Descargas..."),
                bgcolor=BLUE,
            )
            page.snack_bar.open = True
            page.update()
            
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_name = f"npic_backup_{timestamp}.json"
                
                # Exportar a carpeta de Descargas - Compatible con Android
                try:
                    # Intentar Android primero
                    download_dir = Path("/storage/emulated/0/Download")
                    if not download_dir.exists():
                        # Fallback a Downloads normal
                        download_dir = Path.home() / "Downloads"
                    download_dir.mkdir(parents=True, exist_ok=True)
                    export_path = download_dir / export_name
                except Exception:
                    # Si falla, usar Documents como último recurso
                    download_dir = Path.home() / "Documents" / "NPICMemoryDates" / "backups"
                    download_dir.mkdir(parents=True, exist_ok=True)
                    export_path = download_dir / export_name

                # Obtener datos desde StorageService y guardarlos en JSON
                json_data = storage.exportar_datos_json()
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write(json_data)
                
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✅ ¡BACKUP EXPORTADO CON ÉXITO!\n\nArchivo: {export_name}\nUbicación: {export_path.parent}", size=11),
                    bgcolor=GREEN,
                    duration=10000,
                )
            except Exception as ex:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"❌ Error: {str(ex)}"),
                    bgcolor=RED,
                    duration=4000,
                )
            page.snack_bar.open = True
            page.update()
        
        page.add(
            ft.Row([
                create_button("← Volver", back_menu, bgcolor=SUBTEXT, width=120, height=48),
                ft.Text("💾 Exportar backup", size=18, weight="bold", color=ACCENT, expand=True),
            ], spacing=8)
        )
        page.add(ft.Container(height=12))
        
        page.add(
            ft.Text("¿Dónde quieres guardar el backup?", size=15, weight="bold", color=TEXT)
        )
        page.add(ft.Container(height=16))
        
        # Opción 1: Carpeta de la app
        page.add(
            create_card(
                ft.Column([
                    ft.Text("📁 Carpeta de la app", size=16, weight="bold", color=ACCENT),
                    ft.Container(height=8),
                    ft.Text("Documents/NPICMemoryDates/backups", size=12, color=SUBTEXT),
                    ft.Container(height=4),
                    ft.Text("• Backups organizados\n• Se muestra en lista de importar", size=11, color=TEXT),
                ], spacing=2),
                on_click=exportar_carpeta_app,
                border_color=GREEN,
                bgcolor=f"{GREEN}10",
            )
        )
        page.add(ft.Container(height=12))
        
        # Opción 2: Descargas
        page.add(
            create_card(
                ft.Column([
                    ft.Text("📥 Carpeta Descargas", size=16, weight="bold", color=ACCENT),
                    ft.Container(height=8),
                    ft.Text(str(Path.home() / "Downloads"), size=12, color=SUBTEXT),
                    ft.Container(height=4),
                    ft.Text("• Fácil de encontrar\n• Ideal para compartir", size=11, color=TEXT),
                ], spacing=2),
                on_click=exportar_descargas,
                border_color=BLUE,
                bgcolor=f"{BLUE}10",
            )
        )
    
    def show_home():
        # Header con buscador mejorado
        def handle_search(query):
            print(f"DEBUG: handle_search llamado con query='{query}'")
            # Solo buscar cuando el usuario confirme (botón/Enter)
            if not query or len(query.strip()) == 0:
                print("DEBUG: Query vacío, mostrando advertencia")
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Escribe algo para buscar"),
                    bgcolor=ORANGE,
                )
                page.snack_bar.open = True
                page.update()
                return

            try:
                print(f"DEBUG: Buscando equipos con query='{query.strip()}'")
                resultados = buscar_equipos(query.strip())
                print(f"DEBUG: Búsqueda completada, {len(resultados)} resultados encontrados")
                if resultados:
                    print(f"DEBUG: Mostrando resultados: {resultados}")
                    show_view(show_search_results, resultados, query.strip())
                else:
                    print("DEBUG: Sin resultados, pero mostrando pantalla de búsqueda")
                    show_view(show_search_results, [], query.strip())
            except Exception as e:
                print(f"ERROR de búsqueda: {e}")
                import traceback
                traceback.print_exc()
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error en búsqueda: {str(e)}"),
                    bgcolor=RED,
                )
                page.snack_bar.open = True
                page.update()
        
        search_field = ft.TextField(
            hint_text="🔍 Buscar equipo...",
            expand=True,
            height=48,
            text_size=15,
            border_color=ACCENT,
            on_submit=lambda e: handle_search(search_field.value),
        )

        # Botón de búsqueda, algo más compacto pero legible
        buscar_button = ft.Button(
            content=ft.Text("Buscar", size=13, weight="bold"),
            on_click=lambda e: handle_search(search_field.value),
            bgcolor=ACCENT,
            color=TEXT,
            height=48,
            expand=True,
        )
        # Título clicable para mostrar "Acerca de"
        titulo_app = ft.Container(
            content=ft.Text(
                "❄️ NPIC Memory Dates",
                size=24,
                weight="bold",
                color=ACCENT,
                text_align="center",
            ),
            on_click=lambda e: show_view(show_about),
        )

        header = ft.Column(
            [
                titulo_app,
                ft.Text(
                    "Gestión de servicios y mantenimientos de frío",
                    size=13,
                    color=SUBTEXT,
                    text_align="center",
                ),
                ft.Row(
                    [
                        search_field,
                        buscar_button,
                    ],
                    spacing=8,
                    alignment="spaceBetween",
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        create_button("Ver todo", lambda e: show_view(show_all_services), bgcolor=BLUE, height=45),
                        create_button("Historial", lambda e: open_historial_menu(), bgcolor=GREEN, height=45),
                    ],
                    spacing=8,
                    expand=True,
                ),
            ],
            spacing=8,
        )

        # Tarjetas principales (frío)
        cards_frio = ft.Column(
            controls=[
                ft.Row([
                    ft.Container(
                        create_card(
                            ft.Column([
                                ft.Text("❄️", size=45),
                                ft.Text("Frío Positivo", size=17, weight="bold", color=ACCENT),
                                ft.Text("Refrigerados", size=11, color=SUBTEXT),
                            ], horizontal_alignment="center", spacing=6),
                            on_click=lambda e: show_view(show_section, "positivo"),
                            border_color="#FF6B6B",
                        ),
                        expand=1,
                    ),
                    ft.Container(width=12),
                    ft.Container(
                        create_card(
                            ft.Column([
                                ft.Text("🧊", size=45),
                                ft.Text("Frío Negativo", size=17, weight="bold", color=ACCENT),
                                ft.Text("Congelados", size=11, color=SUBTEXT),
                            ], horizontal_alignment="center", spacing=6),
                            on_click=lambda e: show_view(show_section, "negativo"),
                            border_color="#64B5F6",
                        ),
                        expand=1,
                    ),
                ], alignment="spaceBetween", spacing=8),
            ],
            spacing=8,
        )

        # Otras instalaciones (AACC y calor)
        otras_instalaciones_titulo = ft.Text(
            "Otras instalaciones",
            size=15,
            weight="bold",
            color=ACCENT,
        )

        cards_otros = ft.Column([
            ft.Row([
                ft.Container(
                    create_card(
                        ft.Column([
                            ft.Text("🌬️", size=36),
                            ft.Text("AACC < 12 kW", size=12, weight="bold", color=ACCENT),
                            ft.Text("Equipos pequeños", size=10, color=SUBTEXT),
                        ], horizontal_alignment="center", spacing=5),
                        on_click=lambda e: show_view(show_murals, "aacc_lt_12"),
                        border_color="#81D4FA",
                    ),
                    expand=1,
                ),
                ft.Container(width=8),
                ft.Container(
                    create_card(
                        ft.Column([
                            ft.Text("🌬️", size=36),
                            ft.Text("AACC ≥ 12 kW", size=12, weight="bold", color=ACCENT),
                            ft.Text("Equipos grandes", size=10, color=SUBTEXT),
                        ], horizontal_alignment="center", spacing=5),
                        on_click=lambda e: show_view(show_murals, "aacc_gt_12"),
                        border_color="#4FC3F7",
                    ),
                    expand=1,
                ),
            ], spacing=8),
            ft.Row([
                ft.Container(
                    create_card(
                        ft.Column([
                            ft.Text("🔥", size=36),
                            ft.Text("Murales y vitrinas", size=11, weight="bold", color=ACCENT),
                            ft.Text("calientes", size=10, color=SUBTEXT),
                        ], horizontal_alignment="center", spacing=5),
                        on_click=lambda e: show_view(show_murals, "murales_vitrinas_calientes"),
                        border_color="#FF8A65",
                    ),
                    expand=1,
                ),
                ft.Container(width=8),
                ft.Container(
                    create_card(
                        ft.Column([
                            ft.Text("💧", size=36),
                            ft.Text("Fosas sépticas", size=12, weight="bold", color=ACCENT),
                            ft.Text("Saneamiento", size=10, color=SUBTEXT),
                        ], horizontal_alignment="center", spacing=5),
                        on_click=lambda e: show_view(show_murals, "fosas_septicas"),
                        border_color="#4DB6AC",
                    ),
                    expand=1,
                ),
            ], spacing=8),
        ], spacing=8)

        # Sección de alertas destacada
        alert_column = ft.Column(
            controls=[
                ft.Text("⚠️ Requiere Atención", size=16, weight="bold", color=ORANGE),
                ft.Container(height=8),
            ],
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        alert_section = create_card(
            alert_column,
            bgcolor=CARD,
            border_color=ORANGE,
        )

        # Contenedor principal de la home, con scroll interno
        main_column = ft.Column(
            controls=[
                header,
                ft.Container(height=12),
                cards_frio,
                ft.Container(height=16),
                otras_instalaciones_titulo,
                ft.Container(height=8),
                cards_otros,
                ft.Container(height=16),
                alert_section,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
        )

        # Hacer que el contenido se adapte a la altura de la ventana
        page.add(
            ft.Container(
                content=main_column,
                expand=True,
            )
        )
        
        # Alertas simples usando StorageService
        alertas = []
        for eq in storage.data["equipos"]:
            # Buscar último mantenimiento de ese equipo
            mantenimientos_eq = [m for m in storage.data["mantenimientos"] if m["equipo_id"] == eq["id"]]
            if not mantenimientos_eq:
                continue
            ultimo = mantenimientos_eq[-1]
            fecha = ultimo.get("ultima_fecha")
            freq = ultimo.get("frecuencia_dias")
            try:
                if fecha and freq:
                    ultima = datetime.strptime(fecha, "%Y-%m-%d")
                    proxima = ultima + timedelta(days=int(freq))
                    dias = (proxima - datetime.now()).days
                    if dias <= DIAS_ALERTA:
                        alertas.append((eq["nombre"], dias, proxima.strftime("%d/%m/%Y")))
            except Exception:
                continue
        
        if alertas:
            for nombre, dias, proxima in alertas[:5]:
                color = RED if dias < 0 else ORANGE if dias <= 7 else ACCENT
                texto = f"Atrasado {abs(dias)} días" if dias < 0 else f"Quedan {dias} días"

                alerta_pill = ft.Column([
                    ft.Text(texto, size=12, weight="bold", color=color),
                    ft.Text(f"Próx: {proxima}", size=10, color=SUBTEXT),
                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END)

                alert_column.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(nombre, size=13, weight="bold", expand=True),
                            ft.Container(
                                alerta_pill,
                                bgcolor=f"{color}30",
                                padding=8,
                                border_radius=10,
                            ),
                        ]),
                        padding=8,
                        border_radius=10,
                    )
                )
                alert_column.controls.append(ft.Container(height=4))
        else:
            alert_column.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("✅", size=28, color=GREEN),
                        ft.Text("Todo bajo control", size=13, weight="bold", color=GREEN),
                        ft.Text("No hay alertas pendientes", size=11, color=SUBTEXT),
                    ], horizontal_alignment="center", spacing=6),
                    padding=12,
                    border_radius=8,
                    bgcolor=f"{GREEN}20",
                )
            )
    
    def show_about():
        # Vista "Acerca de" al pulsar el título
        def back_home(e):
            # Limpiar el FAB antes de volver
            page.floating_action_button = None
            show_view(show_home)

        def close_app(e):
            if is_web:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Esta acción no está disponible en la versión web"),
                    bgcolor=ORANGE,
                )
                page.snack_bar.open = True
                page.update()
                return
            if threading is None:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("No se puede cerrar la app en este entorno"),
                    bgcolor=ORANGE,
                )
                page.snack_bar.open = True
                page.update()
                return
            try:
                if e and getattr(e, "control", None):
                    e.control.disabled = True
                    if isinstance(getattr(e.control, "content", None), ft.Text):
                        e.control.content.value = "Cerrando..."
                    e.control.update()

                for attr in ("window_close", "close", "window_destroy"):
                    fn = getattr(page, attr, None)
                    if callable(fn):
                        try:
                            fn()
                        except Exception:
                            pass

                page.window_visible = False
                page.update()

                threading.Timer(0.3, lambda: os._exit(0)).start()
            except Exception as exc:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"No se pudo cerrar la app: {exc}"),
                    bgcolor=RED,
                )
                page.snack_bar.open = True
                page.update()
        
        page.add(
            ft.Row([
                create_button("←", back_home, bgcolor=CARD, width=48, height=48),
                ft.Text("ℹ️ Acerca de", size=19, weight="bold", color=ACCENT, expand=True),
                create_button("Cerrar app", close_app, bgcolor=RED, width=150, height=48),
            ], spacing=8)
        )
        page.add(ft.Container(height=12))

        modo_switch = ft.Switch(
            value=is_dark_mode,
            on_change=lambda e: cambiar_tema(e.control.value),
        )

        # Información de almacenamiento según la plataforma
        if is_web:
            storage_info = "Datos guardados en el navegador (localStorage)"
        else:
            docs_dir = Path.home() / "Documents" / "NPICMemoryDates"
            storage_info = str(docs_dir)
        
        info = ft.Column([
            ft.Text("NPIC Memory Dates", size=20, weight="bold", color=ACCENT),
            ft.Container(height=6),
            ft.Text("Creado por Dani GM", size=14, weight="bold", color=TEXT),
            ft.Text("Gestión de servicios y mantenimientos de frío", size=12, color=SUBTEXT),
            ft.Text("Para el equipo de Mdona Hospitalet", size=12, color=SUBTEXT),
            ft.Container(height=12),
            ft.Text(f"Versión 1.0", size=12, color=SUBTEXT),
            ft.Text(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", size=12, color=SUBTEXT),
            ft.Container(height=12),
            ft.Text("💾 Almacenamiento:", size=12, weight="bold", color=ACCENT),
            ft.Text(storage_info, size=10, color=SUBTEXT, selectable=not is_web),
            ft.Container(height=16),
            ft.Row([
                ft.Text("🌙 Modo oscuro", size=13, color=TEXT),
                modo_switch,
                ft.Text("☀️ Modo claro", size=13, color=TEXT),
            ], alignment="start", vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
        ], spacing=4)

        page.add(
            create_card(
                info,
                bgcolor=CARD,
                               border_color=ACCENT,
            )
        )
        
        # Añadir FAB (Floating Action Button) para facilitar navegación en móvil
        if is_narrow_screen():
            page.floating_action_button = ft.FloatingActionButton(
                icon=ft.icons.ARROW_BACK,
                bgcolor=ACCENT,
                on_click=back_home,
                tooltip="Volver al inicio",
            )
            page.update()

    def show_search_results(resultados, query):
        # Header
        def back_home(e):
            show_view(show_home)
        
        if not resultados:
            contenido = ft.Column([
                create_button("← Volver", back_home, bgcolor=SUBTEXT, height=48),
                ft.Container(height=12),
                ft.Text(f"🔍 Búsqueda: '{query}'", size=18, weight="bold", color=ACCENT),
                ft.Container(height=20),
                ft.Column([
                    ft.Text("❌", size=48),
                    ft.Text("Sin resultados", size=16, weight="bold", color=SUBTEXT),
                    ft.Text(f"No se encontró '{query}'", size=12, color=SUBTEXT),
                ], horizontal_alignment="center", spacing=8),
            ], spacing=8, scroll=ft.ScrollMode.AUTO)
        else:
            # Al hacer clic en un resultado, ir al mural (lista de servicios)
            # correspondiente, no directamente a la pantalla de configuración.
            def crear_handler_click(eq):
                def _handler(e):
                    # Usar el tipo si existe; si no, inferirlo del prefijo del nombre
                    tipo = eq.get("tipo") or (eq["nombre"].split("_")[0] if "_" in eq["nombre"] else "")
                    if tipo:
                        show_view(show_murals, tipo)
                    else:
                        # Como último recurso, ir a la pantalla de detalles
                        show_view(show_equipo_details, eq["nombre"], None)
                return _handler

            resultado_cards = []
            for equipo in resultados:
                resultado_cards.append(
                    create_card(
                        ft.Column([
                            ft.Text(equipo["nombre"], size=14, weight="bold", color=ACCENT),
                            ft.Text(f"📍 {equipo['seccion']} / {equipo['tipo']}", size=11, color=SUBTEXT),
                        ], spacing=2),
                        on_click=crear_handler_click(equipo),
                        border_color=ACCENT
                    )
                )

            contenido = ft.Column([
                create_button("← Volver", back_home, bgcolor=SUBTEXT, height=48),
                ft.Container(height=8),
                ft.Text(f"🔍 Resultados: '{query}'", size=18, weight="bold", color=ACCENT),
                ft.Text(f"{len(resultados)} equipos encontrados", size=12, color=SUBTEXT),
                ft.Container(height=12),
                ft.Column(
                    controls=resultado_cards,
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ], spacing=8, scroll=ft.ScrollMode.AUTO)
        
        clear_page()
        page.add(contenido)
        page.update()
    
    def show_section(seccion):
        # Header
        page.add(
            ft.Row([
                ft.Container(
                    content=ft.Row([
                        ft.Text("←", size=18, color=ACCENT),
                        ft.Text("Volver", size=14, weight="bold", color=ACCENT),
                    ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                    on_click=lambda e: show_view(show_home),
                    bgcolor=CARD,
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    border_radius=10,
                    border=ft.Border.all(2, ACCENT),
                    height=48,
                ),
                ft.Text(
                    "❄️ Frío Positivo" if seccion == "positivo" else "🧊 Frío Negativo",
                    size=20, weight="bold", color=ACCENT, expand=True
                ),
            ], spacing=8)
        )
        page.add(ft.Container(height=12))
        
        # Áreas
        areas = []
        if seccion == "positivo":
            areas = [
                ("🥩 Murales Carne", "carne", "#FF6B6B"),
                ("🐟 Murales Pescado", "pescado", "#4ECDC4"),
                ("🥦 Murales Verdura", "verdura", "#81C784"),
                ("🥛 Murales Lácteos", "lacteos", "#FFD93D"),
                ("🥓 Murales Charcutería", "charcuteria", "#FFB3A7"),
                ("🥤 Bebidas frías", "bebidas_frias", "#4FC3F7"),
                ("🥛 Leche fresca", "leche_fresca", "#FFF59D"),
                ("🧃 Zumos", "zumos", "#FFCC80"),
                ("🍽️ Platos preparados", "platos_preparados", "#CE93D8"),
                ("🥗 Vitrina LPC libre servicio", "vitrina_lpc_ls", "#AED581"),
                ("🍱 Mostrador LPC", "mostrador_lpc", "#FFAB91"),
                ("🥗 Murales listos para comer", "murales_lpc", "#80CBC4"),
                ("🍣 Mural Sushi", "mural_sushi", "#FFCCBC"),
                ("🥗 Mural Ensaladas", "mural_ensaladas", "#A5D6A7"),
                ("🚪 Cámaras de refrigerado", "camaras_refrigerado", "#9FA8DA"),
                ("🏭 Central frigorífica positiva", "central_frigorifica_positiva", "#B39DDB"),
            ]
        else:
            areas = [
                ("🥩 Isla Carne Congelada", "isla_carne", "#FF8A8A"),
                ("🦐 Isla de Marisco congelado", "isla_marisco_congelado", "#80CBC4"),
                ("🥦 Isla Verdura Congelada", "isla_verdura", "#A8E6CF"),
                ("🗄️ Armarios Verdura congelada", "armarios_verdura congelada", "#6BCF7F"),
                ("🐟 Isla Pescado Congelado", "isla_pescado", "#64B5F6"),
                ("🐟 Armarios Pescado Congelado", "armarios_pescado_congelado", "#90CAF9"),
                ("🍰 Isla de Tartas", "isla_tartas", "#FFCDD2"),
                ("🍨 Islas Helados", "isla_helados", "#F48FB1"),
                ("🚪 Cámaras de congelado", "camaras_congelado", "#B0BEC5"),
                ("🏭 Central frigorífica negativa", "central_frigorifica_negativa", "#B0BEC5"),
            ]
        
        for title, kind, color in areas:
            page.add(
                create_card(
                    ft.Row([
                        ft.Text(title, size=14, weight="bold", color=ACCENT, expand=True),
                        ft.Text("→", size=18, color=color),
                    ], spacing=8),
                    border_color=color,
                    on_click=lambda e, k=kind: show_view(show_murals, k),
                )
            )
            page.add(ft.Container(height=6))

    def show_all_services():
        # Header
        page.add(
            ft.Row([
                ft.Container(
                    content=ft.Row([
                        ft.Text("←", size=18, color=ACCENT),
                        ft.Text("Volver", size=14, weight="bold", color=ACCENT),
                    ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                    on_click=lambda e: show_view(show_home),
                    bgcolor=CARD,
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    border_radius=10,
                    border=ft.Border.all(2, ACCENT),
                    height=48,
                ),
                ft.Text("📋 Todos los servicios", size=19, weight="bold", color=ACCENT, expand=True),
            ], spacing=8)
        )
        page.add(ft.Container(height=12))

        # Obtener todos los equipos desde StorageService
        equipos = storage.get_all_equipos()

        if not equipos:
            page.add(
                create_card(
                    ft.Column([
                        ft.Text("📭", size=36),
                        ft.Text("Sin servicios", size=15, weight="bold", color=ACCENT),
                    ], horizontal_alignment="center", spacing=6)
                )
            )
            return

        for nombre, seccion, tipo, posicion in equipos:
            data = get_equipo_data(nombre)
            dias, proxima_str = calculate_days(nombre)

            # Solo mostrar servicios con fecha/frecuencia configuradas
            if dias is None:
                continue

            if dias < 0:
                estado_text = f"Atrasado {abs(dias)} días"
                estado_color = RED
            elif dias <= DIAS_ALERTA:
                estado_text = f"Quedan {dias} días"
                estado_color = ORANGE
            else:
                estado_text = f"Quedan {dias} días"
                estado_color = GREEN

            pos_num = (posicion + 1) if posicion is not None else "-"

            # Recuadro de estado grande y alargado, con próxima fecha destacada
            estado_col = ft.Column([
                ft.Text(estado_text, size=14, weight="bold", color=TEXT),
            ], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            if proxima_str:
                estado_col.controls.append(
                    ft.Text(f"Vence: {proxima_str}", size=12, weight="bold", color=TEXT)
                )

            page.add(
                create_card(
                    ft.Column([
                        ft.Row([
                            ft.Text(str(pos_num), size=12, weight="bold", color=SUBTEXT, text_align="center"),
                            ft.Column([
                                ft.Text(nombre, size=13, weight="bold", color=ACCENT),
                                ft.Text(f"{seccion} / {tipo}", size=11, color=SUBTEXT),
                            ], expand=True, spacing=2),
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                        ft.Container(
                            estado_col,
                            bgcolor=f"{estado_color}CC",
                            padding=10,
                            border_radius=12,
                        ),
                    ], spacing=8),
                    on_click=lambda e, n=nombre, k=tipo: show_view(show_equipo_details, n, k),
                    border_color=ACCENT,
                )
            )
            page.add(ft.Container(height=6))
    
    def show_murals(kind):
        # Header
        positivos = [
            "carne",
            "pescado",
            "verdura",
            "lacteos",
            "charcuteria",
            "bebidas_frias",
            "leche_fresca",
            "zumos",
            "platos_preparados",
            "vitrina_lpc_ls",
            "mostrador_lpc",
            "murales_lpc",
            "mural_sushi",
            "mural_ensaladas",
            "camaras_refrigerado",
            "central_frigorifica_positiva",
        ]
        negativos = [
            "isla_carne",
            "isla_verdura",
            "armario_verdura",
            "isla_pescado",
            "isla_helados",
            "armario_pescado_congelado",
            "isla_marisco",
            "isla_tartas",
            "camaras_congelado",
            "central_frigorifica_negativa",
        ]

        if kind in positivos:
            back_fn = lambda e: show_view(show_section, "positivo")
        elif kind in negativos:
            back_fn = lambda e: show_view(show_section, "negativo")
        else:
            # AACC y murales/vitrinas calientes vuelven al inicio
            back_fn = lambda e: show_view(show_home)

        title_map = {
            "aacc_lt_12": "AACC < 12 kW",
            "aacc_gt_12": "AACC ≥ 12 kW",
            "murales_vitrinas_calientes": "Murales y vitrinas calientes",
            "fosas_septicas": "Fosas sépticas",
        }
        titulo = title_map.get(kind, kind.replace("_", " ").title())

        page.add(
            ft.Row([
                ft.Container(
                    content=ft.Row([
                        ft.Text("←", size=18, color=ACCENT),
                        ft.Text("Volver", size=14, weight="bold", color=ACCENT),
                    ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                    on_click=back_fn,
                    bgcolor=CARD,
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    border_radius=10,
                    border=ft.Border.all(2, ACCENT),
                    height=48,
                ),
                ft.Text(titulo, size=19, weight="bold", color=ACCENT, expand=True),
                create_button("+", lambda e: open_add_dialog(kind), bgcolor=GREEN, width=48, height=48),
            ], spacing=8)
        )
        page.add(ft.Container(height=12))
        
        # Equipos
        equipos = get_equipos_por_tipo(kind)
        lista_nombres = list(equipos.keys())
        total_equipos = len(lista_nombres)
        
        # Mapeo de colores por tipo
        color_map = {
            "carne": "#FF8A7B",
            "pescado": "#5AC8FA",
            "verdura": "#7ED321",
            "lacteos": "#FFD426",
            "charcuteria": "#FFB3A7",
            "bebidas_frias": "#4FC3F7",
            "leche_fresca": "#FFF59D",
            "zumos": "#FFCC80",
            "platos_preparados": "#CE93D8",
            "vitrina_lpc_ls": "#AED581",
            "mostrador_lpc": "#FFAB91",
            "murales_lpc": "#80CBC4",
            "mural_sushi": "#FFCCBC",
            "mural_ensaladas": "#A5D6A7",
            "camaras_refrigerado": "#9FA8DA",
            "central_frigorifica_positiva": "#B39DDB",
            "aacc_lt_12": "#81D4FA",
            "aacc_gt_12": "#4FC3F7",
            "murales_vitrinas_calientes": "#FF8A65",
            "fosas_septicas": "#4DB6AC",
            "isla_carne": "#FF6B6B",
            "isla_verdura": "#81C784",
            "armario_verdura": "#66BB6A",
            "isla_pescado": "#42A5F5",
            "isla_helados": "#F48FB1",
            "armario_pescado_congelado": "#90CAF9",
            "isla_marisco": "#80CBC4",
            "isla_tartas": "#FFCDD2",
            "camaras_congelado": "#B0BEC5",
            "central_frigorifica_negativa": "#B0BEC5",
        }
        
        border_color = color_map.get(kind, ACCENT)
        
        for idx, nombre in enumerate(lista_nombres):
            data = equipos[nombre]
            dias, proxima_str = calculate_days(nombre)
            
            # Determinar estado
            if dias is None or data["date"] is None:
                estado_text = "No configurado"
                estado_color = SUBTEXT
            else:
                if dias < 0:
                    estado_text = f"Atrasado {abs(dias)} días"
                    estado_color = RED
                elif dias == 0:
                    estado_text = "¡Vence hoy!"
                    estado_color = RED
                elif dias <= DIAS_ALERTA:
                    estado_text = f"Quedan {dias} días"
                    estado_color = ORANGE
                else:
                    estado_text = f"Quedan {dias} días"
                    estado_color = GREEN
            
            # Emoji - mapeo completo por tipo
            emoji_map = {
                "carne": "🥩",
                "pescado": "🐟",
                "verdura": "🥦",
                "lacteos": "🥛",
                "charcuteria": "🥓",
                "bebidas_frias": "🥤",
                "leche_fresca": "🥛",
                "zumos": "🧃",
                "platos_preparados": "🍽️",
                "vitrina_lpc_ls": "🥗",
                "mostrador_lpc": "🍱",
                "murales_lpc": "🥗",
                "mural_sushi": "🍣",
                "mural_ensaladas": "🥗",
                "camaras_refrigerado": "🚪",
                "central_frigorifica_positiva": "❄️",
                "aacc_lt_12": "❄️",
                "aacc_gt_12": "❄️",
                "murales_vitrinas_calientes": "🔥",
                "fosas_septicas": "🚰",
                "isla_carne": "🥩",
                "isla_verdura": "🥦",
                "armario_verdura": "🗄️",
                "isla_pescado": "🐟",
                "isla_helados": "🍨",
                "armario_pescado_congelado": "🐟",
                "isla_marisco": "🦐",
                "isla_tartas": "🍰",
                "camaras_congelado": "🚪",
                "central_frigorifica_negativa": "🧊",
            }
            emoji = emoji_map.get(kind, "🧊")

            # Nota asociada (para colorear el botón de nota y tooltip)
            nota_texto = (data.get("nota") or "").strip()
            tiene_nota = len(nota_texto) > 0
            nota_bg = f"{ACCENT}30" if tiene_nota else f"{SUBTEXT}20"
            nota_tooltip = nota_texto if tiene_nota else "Añadir nota"
            
            # Número del equipo basado en posicion almacenada (mantiene huecos)
            try:
                num = int(data.get("posicion") or 0) + 1
            except Exception:
                num = idx + 1
            
            # Contenedor con estado (texto + próxima fecha) muy visible para móvil
            estado_col = ft.Column(
                [
                    ft.Text(estado_text, size=15, color=TEXT, weight="bold"),
                ],
                spacing=3,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            if proxima_str:
                estado_col.controls.append(
                    ft.Text(f"Vence: {proxima_str}", size=13, color=TEXT, weight="bold"),
                )

            # Botones de acción en fila horizontal
            botones_row = ft.Row([
                # Botón Arriba (solo si no es el primero)
                ft.Container(
                    content=ft.Text("⬆️", size=14),
                    on_click=lambda e, n=nombre, k=kind, i=idx: (change_equipo_position(n, "arriba"), show_view(show_murals, k)) if i > 0 else None,
                    padding=5,
                    tooltip="Mover arriba",
                    border_radius=6,
                    bgcolor=f"{ACCENT if idx > 0 else SUBTEXT}20",
                    opacity=1 if idx > 0 else 0.5,
                ),
                # Botón Abajo (solo si no es el último)
                ft.Container(
                    content=ft.Text("⬇️", size=14),
                    on_click=lambda e, n=nombre, k=kind, i=idx: (change_equipo_position(n, "abajo"), show_view(show_murals, k)) if i < total_equipos - 1 else None,
                    padding=5,
                    tooltip="Mover abajo",
                    border_radius=6,
                    bgcolor=f"{ACCENT if idx < total_equipos - 1 else SUBTEXT}20",
                    opacity=1 if idx < total_equipos - 1 else 0.5,
                ),
                # Botón Nota
                ft.Container(
                    content=ft.Text("📝", size=14),
                    on_click=lambda e, n=nombre, k=kind: open_note_dialog(n, k),
                    padding=5,
                    tooltip=nota_tooltip,
                    border_radius=6,
                    bgcolor=nota_bg,
                ),
                # Botón Editar
                ft.Container(
                    content=ft.Text("✏️", size=14),
                    on_click=lambda e, n=nombre: open_edit_dialog(n, kind),
                    padding=5,
                    tooltip="Editar nombre",
                    border_radius=6,
                    bgcolor=f"{ACCENT}20",
                ),
                # Botón Eliminar (siempre disponible)
                ft.Container(
                    content=ft.Text("🗑️", size=14),
                    on_click=lambda e, n=nombre, k=kind: confirm_delete(n, k),
                    padding=5,
                    tooltip="Eliminar servicio",
                    border_radius=6,
                    bgcolor=f"{RED}20",
                ),
            ], spacing=4)

            # Tarjeta del equipo - diseño responsive
            card = create_card(
                ft.Column([
                        # Nombre completo y emoji - clickeable
                        ft.Container(
                            content=ft.Row([
                                ft.Text(emoji, size=22),
                                ft.Column([
                                    ft.Text(nombre, size=14, weight="bold", color=ACCENT),
                                    ft.Text(f"Pos: {num}", size=11, color=SUBTEXT),
                                ], expand=True, spacing=0),
                            ], spacing=8),
                            on_click=lambda e, n=nombre, k=kind: show_view(show_equipo_details, n, k),
                        ),

                        # Estado (texto + próxima fecha) en recuadro
                        ft.Container(
                            estado_col,
                            bgcolor=f"{estado_color}CC",
                            padding=8,
                            border_radius=12,
                            width=float("inf"),
                        ),
                        
                        # Botones de acción en fila
                        botones_row,
                    ], spacing=5),
                border_color=border_color,
                on_click=lambda e, n=nombre, k=kind: show_view(show_equipo_details, n, k),
            )

            page.add(card)
            page.add(ft.Container(height=4))
    
    def open_edit_dialog(equipo_nombre, kind):
        # Guardar referencia a la página actual
        original_controls = page.controls.copy()
        
        nuevo_nombre_field = ft.TextField(
            label="Nuevo nombre",
            value=equipo_nombre,
            expand=True,
            height=48,
            text_size=14,
            autofocus=True
        )
        
        mensaje_text = ft.Text("", size=13)
        
        def guardar_cambios(e):
            nuevo_nombre = nuevo_nombre_field.value.strip()
            
            if not nuevo_nombre:
                mensaje_text.value = "El nombre no puede estar vacío"
                mensaje_text.color = ORANGE
                mensaje_text.update()
                return

            if nuevo_nombre == equipo_nombre:
                # Sin cambios
                cancelar(e)
                return
            
            ok, msg = rename_equipo(equipo_nombre, nuevo_nombre)
            if ok:
                show_view(show_murals, kind)
            else:
                mensaje_text.value = msg
                mensaje_text.color = RED
                mensaje_text.update()
        
        def cancelar(e):
            # Restaurar controles originales
            page.controls.clear()
            for control in original_controls:
                page.controls.append(control)
            page.update()
        
        # Crear diálogo
        dialog_content = ft.Column([
            ft.Text("✏️ Editar Nombre", size=17, weight="bold", color=ACCENT),
            ft.Container(height=12),
            nuevo_nombre_field,
            ft.Container(height=8),
            mensaje_text,
            ft.Container(height=12),
            ft.Row([
                create_button("Cancelar", cancelar, bgcolor=SUBTEXT, height=48),
                create_button("Guardar", guardar_cambios, bgcolor=GREEN, height=48),
            ], spacing=8)
        ], spacing=4)
        
        # Mostrar diálogo centrado
        clear_page()
        page.add(
            ft.Column(
                [
                    ft.Container(
                        content=dialog_content,
                        bgcolor=CARD,
                        padding=16,
                        border_radius=15,
                        border=ft.Border.all(3, ACCENT),
                        expand=True,
                    )
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        page.update()

    def open_note_dialog(equipo_nombre, kind):
        """Diálogo para añadir/editar/eliminar nota de un servicio."""
        # Guardar referencia a la página actual
        original_controls = page.controls.copy()

        nota_actual = get_nota_equipo(equipo_nombre)

        nota_field = ft.TextField(
            label="Nota (máx 50 caracteres)",
            value=nota_actual,
            expand=True,
            height=120,
            max_length=50,
            multiline=True,
            text_size=14,
        )

        mensaje_text = ft.Text("", size=13)

        def guardar_nota(e):
            texto = (nota_field.value or "").strip()
            if len(texto) > 50:
                mensaje_text.value = "La nota no puede superar 50 caracteres"
                mensaje_text.color = ORANGE
                mensaje_text.update()
                return

            if not set_nota_equipo(equipo_nombre, texto):
                mensaje_text.value = "No se pudo guardar la nota"
                mensaje_text.color = RED
                mensaje_text.update()
                return

            # Volver a la vista de murales del tipo correspondiente
            show_view(show_murals, kind)

        def eliminar_nota(e):
            set_nota_equipo(equipo_nombre, "")
            show_view(show_murals, kind)

        def cancelar(e):
            # Restaurar controles originales
            page.controls.clear()
            for control in original_controls:
                page.controls.append(control)
            page.update()

        dialog_content = ft.Column([
            ft.Text("📝 Nota del servicio", size=17, weight="bold", color=ACCENT),
            ft.Container(height=12),
            nota_field,
            ft.Container(height=8),
            mensaje_text,
            ft.Container(height=12),
            ft.Row([
                create_button("Cancelar", cancelar, bgcolor=SUBTEXT, height=48),
                create_button("Eliminar", eliminar_nota, bgcolor=RED, height=48),
                create_button("Guardar", guardar_nota, bgcolor=GREEN, height=48),
            ], spacing=8),
        ], spacing=4)

        clear_page()
        page.add(
            ft.Column(
                [
                    ft.Container(
                        content=dialog_content,
                        bgcolor=CARD,
                        padding=16,
                        border_radius=15,
                        border=ft.Border.all(3, ACCENT),
                        expand=True,
                    )
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        page.update()
    
    def confirm_delete(equipo_nombre, kind):
        # Guardar referencia a la página actual
        original_controls = page.controls.copy()
        
        def eliminar(e):
            if delete_equipo(equipo_nombre):
                show_view(show_murals, kind)
            else:
                # Si hay error, restaurar vista
                page.controls.clear()
                for control in original_controls:
                    page.controls.append(control)
                page.update()
        
        def cancelar(e):
            # Restaurar controles originales
            page.controls.clear()
            for control in original_controls:
                page.controls.append(control)
            page.update()
        
        # Crear diálogo de confirmación
        dialog_content = ft.Column([
            ft.Text("🗑️ Eliminar Equipo", size=17, weight="bold", color=RED),
            ft.Container(height=12),
            ft.Text(f"¿Eliminar {equipo_nombre}?", size=14, weight="bold", text_align="center"),
            ft.Text("Esta acción no se puede deshacer", size=12, color=SUBTEXT, text_align="center"),
            ft.Container(height=16),
            ft.Row([
                create_button("Cancelar", cancelar, bgcolor=SUBTEXT, height=48),
                create_button("Eliminar", eliminar, bgcolor=RED, height=48),
            ], spacing=8)
        ], spacing=4)
        
        # Mostrar diálogo centrado
        clear_page()
        page.add(
            ft.Column(
                [
                    ft.Container(
                        content=dialog_content,
                        bgcolor=CARD,
                        padding=16,
                        border_radius=15,
                        border=ft.Border.all(3, RED),
                        expand=True,
                    )
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )
        page.update()
    
    def open_add_dialog(kind):
        # Guardar referencia a la página actual
        original_controls = page.controls.copy()
        
        # Campo para indicar cuántos servicios crear de golpe
        cantidad_field = ft.TextField(
            label="Nº servicios",
            value="",
            expand=True,
            height=48,
            text_size=14,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # Posiciones posibles: hasta 10. Se permite elegir posición aunque haya huecos;
        # si el usuario elige más allá del final, se inserta al final.
        equipos_existentes = get_equipos_por_tipo(kind)
        total_equipos = len(equipos_existentes)
        max_slots = 10
        max_posicion = max_slots  # mostrar siempre hasta 10

        posicion_field = ft.Dropdown(
            label="Posición (solo 1 servicio)",
            expand=True,
            options=[ft.dropdown.Option(str(i)) for i in range(1, max_posicion + 1)],
            value=str(min(total_equipos + 1, max_slots)),
        )

        posicion_container = ft.Container(posicion_field)

        # Campos de nombre dinámicos para varios servicios
        nombre_fields = []
        nombres_column = ft.Column(spacing=6)

        mensaje_text = ft.Text("", size=13)

        def actualizar_campos(e=None):
            # Recalcular slots libres
            equipos_actuales = get_equipos_por_tipo(kind)
            total_actual = len(equipos_actuales)
            libres = max_slots - total_actual

            if libres <= 0:
                cantidad_field.value = "0"
                mensaje_text.value = "Zona completa: máximo 10 servicios"
                mensaje_text.color = RED
                nombre_fields.clear()
                nombres_column.controls.clear()
                cantidad_field.update()
                nombres_column.update()
                mensaje_text.update()
                posicion_container.visible = False
                posicion_container.update()
                return

            # Permitir borrar el campo sin que se rellene solo
            try:
                n = int((cantidad_field.value or "").strip())
            except ValueError:
                # Si está vacío o no es número, no cambiamos nada
                nombre_fields.clear()
                nombres_column.controls.clear()
                nombres_column.update()
                posicion_container.visible = False
                posicion_container.update()
                return

            if n < 1:
                n = 1
            if n > libres:
                n = libres

            # Posición solo tiene sentido si n == 1
            posicion_container.visible = (n == 1)
            posicion_container.update()

            nombre_fields.clear()
            nombres_column.controls.clear()
            for i in range(n):
                tf = ft.TextField(
                    label=f"Nombre servicio {i + 1}",
                    hint_text="Ej: 1, central, mural nuevo",
                    expand=True,
                    height=48,
                    text_size=14,
                    autofocus=(i == 0),
                )
                nombre_fields.append(tf)
                nombres_column.controls.append(tf)
            nombres_column.update()

        cantidad_field.on_change = actualizar_campos

        def guardar_equipo(e):
            # Recalcular número actual de equipos por seguridad
            equipos_actuales = get_equipos_por_tipo(kind)
            total_actual = len(equipos_actuales)
            libres = max_slots - total_actual

            if libres <= 0:
                mensaje_text.value = "Solo se permiten 10 servicios en esta zona"
                mensaje_text.color = RED
                mensaje_text.update()
                return

            # Filtrar nombres no vacíos
            nombres_validos = [
                (i, (tf.value or "").strip())
                for i, tf in enumerate(nombre_fields)
                if (tf.value or "").strip()
            ]

            if not nombres_validos:
                mensaje_text.value = "Escribe al menos un nombre de servicio"
                mensaje_text.color = ORANGE
                mensaje_text.update()
                return

            if len(nombres_validos) > libres:
                nombres_validos = nombres_validos[:libres]

            # Posición elegida (solo aplica si estamos creando exactamente un servicio)
            try:
                pos_ui = int(posicion_field.value or "1")
            except ValueError:
                pos_ui = total_actual + 1

            if pos_ui < 1:
                pos_ui = 1
            if pos_ui > max_slots:
                pos_ui = max_slots
            if pos_ui > total_actual + 1:
                # si escoge una posición más allá del final, se inserta al final actual
                pos_ui = total_actual + 1

            positivos = [
                "carne",
                "pescado",
                "verdura",
                "lacteos",
                "charcuteria",
                "bebidas_frias",
                "leche_fresca",
                "zumos",
                "platos_preparados",
                "vitrina_lpc_ls",
                "mostrador_lpc",
                "murales_lpc",
                "mural_sushi",
                "mural_ensaladas",
                "camaras_refrigerado",
                "central_frigorifica_positiva",
            ]
            negativos = [
                "isla_carne",
                "isla_verdura",
                "armario_verdura",
                "isla_pescado",
                "isla_helados",
                "armario_pescado_congelado",
                "isla_marisco",
                "isla_tartas",
                "camaras_congelado",
                "central_frigorifica_negativa",
            ]

            if kind in positivos:
                seccion = "positivo"
            elif kind in negativos:
                seccion = "negativo"
            elif kind.startswith("aacc_"):
                seccion = "aacc"
            elif kind == "murales_vitrinas_calientes":
                seccion = "caliente"
            elif kind == "fosas_septicas":
                seccion = "fosas"
            else:
                seccion = "otro"

            creados = 0
            pos_index_base = pos_ui - 1

            for offset, (_, nombre_srv) in enumerate(nombres_validos):
                # Si hay más de un servicio, los vamos colocando uno detrás de otro
                if len(nombres_validos) == 1:
                    pos_index = pos_index_base
                else:
                    pos_index = total_actual + creados

                if insert_equipo_at_position(kind, nombre_srv, seccion, pos_index):
                    creados += 1
                else:
                    mensaje_text.value = "Algún servicio ya existe o no se pudo crear"
                    mensaje_text.color = ORANGE
                    mensaje_text.update()

            if creados > 0:
                show_view(show_murals, kind)
            else:
                if not mensaje_text.value:
                    mensaje_text.value = "No se pudo crear ningún servicio"
                    mensaje_text.color = RED
                    mensaje_text.update()
        
        def cancelar(e):
            # Restaurar controles originales
            page.controls.clear()
            for control in original_controls:
                page.controls.append(control)
            page.update()
        
        # Crear diálogo
        dialog_content = ft.Column([
            ft.Text("➕ Nuevo(s) Servicio(s)", size=17, weight="bold", color=GREEN),
            ft.Container(height=12),
            cantidad_field,
            ft.Container(height=8),
            posicion_container,
            ft.Container(height=8),
            nombres_column,
            ft.Container(height=8),
            mensaje_text,
            ft.Container(height=12),
            ft.Row([
                create_button("Cancelar", cancelar, bgcolor=SUBTEXT, height=48),
                create_button("Agregar", guardar_equipo, bgcolor=GREEN, height=48),
            ], spacing=8)
        ], spacing=0)

        # Mostrar diálogo centrado
        clear_page()
        page.add(
            ft.Column(
                [
                    ft.Container(
                        content=ft.Column([dialog_content], scroll=ft.ScrollMode.AUTO),
                        bgcolor=CARD,
                        padding=16,
                        border_radius=15,
                        border=ft.Border.all(3, GREEN),
                        expand=True,
                    )
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        page.update()

        # Inicializar los campos de nombre una vez que el diálogo ya está en la página
        actualizar_campos()
    
    def show_equipo_details(equipo_nombre, kind_param=None):
        # Usar el kind pasado o extraerlo del nombre
        if kind_param is not None:
            kind = kind_param
        elif "_" in equipo_nombre:
            kind = equipo_nombre.split("_")[0]
        else:
            kind = ""
        
        page.add(
            ft.Row([
                ft.Container(
                    content=ft.Row([
                        ft.Text("←", size=18, color=ACCENT),
                        ft.Text("Volver", size=14, weight="bold", color=ACCENT),
                    ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                    on_click=lambda e: show_view(show_murals, kind) if kind else show_view(show_home),
                    bgcolor=CARD,
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    border_radius=10,
                    border=ft.Border.all(2, ACCENT),
                    height=48,
                ),
                ft.Text(f"⚙️ {equipo_nombre}", size=18, weight="bold", color=ACCENT, expand=True),
            ], spacing=8)
        )
        page.add(ft.Container(height=16))
        
        # Obtener datos
        equipo_data = get_equipo_data(equipo_nombre)
        fecha_actual = equipo_data["date"] if equipo_data and equipo_data["date"] else ""
        frecuencia_actual = str(equipo_data["freq"]) if equipo_data and equipo_data["freq"] else ""
        
        # Campo de fecha (formato YYYY-MM-DD)
        fecha_field = ft.TextField(
            label="Último mantenimiento (YYYY-MM-DD)",
            value="",
            expand=True,
            height=48,
            text_size=14,
            border_color=ACCENT,
        )

        # DatePicker clásico: se abre poniendo open=True
        date_picker = ft.DatePicker(
            first_date=datetime(2000, 1, 1),
            last_date=datetime(2100, 12, 31),
        )

        def on_date_change(e):
            try:
                if date_picker.value:
                    # En versiones antiguas value suele ser datetime.date
                    valor = date_picker.value
                    if isinstance(valor, str):
                        fecha_field.value = valor
                    else:
                        fecha_field.value = valor.strftime("%Y-%m-%d")
                    fecha_field.update()
            except Exception:
                pass

        date_picker.on_change = on_date_change
        if date_picker not in page.overlay:
            page.overlay.append(date_picker)
        
        frecuencia_field = ft.TextField(
            label="Frecuencia (días)",
            value="",
            expand=True,
            height=48,
            text_size=14,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=ACCENT,
        )
        
        mensaje_text = ft.Text("", size=12)

        def reset_campos(e):
            if reset_mantenimiento(equipo_nombre):
                fecha_field.value = ""
                frecuencia_field.value = ""
                mensaje_text.value = "Campos restablecidos"
                mensaje_text.color = GREEN
            else:
                mensaje_text.value = "No se pudo restablecer"
                mensaje_text.color = RED
            fecha_field.update()
            frecuencia_field.update()
            mensaje_text.update()
        
        def guardar(e):
            fecha = fecha_field.value.strip()
            frecuencia = frecuencia_field.value.strip()
            
            if not fecha or not frecuencia:
                mensaje_text.value = "⚠️ Completa ambos campos"
                mensaje_text.color = ORANGE
                mensaje_text.update()
                return
            
            try:
                datetime.strptime(fecha, "%Y-%m-%d")
                freq_int = int(frecuencia)
                if freq_int <= 0:
                    mensaje_text.value = "⚠️ Frecuencia debe ser > 0"
                    mensaje_text.color = ORANGE
                    mensaje_text.update()
                    return
            except ValueError:
                mensaje_text.value = "❌ Fecha debe ser YYYY-MM-DD"
                mensaje_text.color = RED
                mensaje_text.update()
                return
            
            if save_mantenimiento(equipo_nombre, fecha, freq_int):
                mensaje_text.value = "✅ Guardado correctamente"
                mensaje_text.color = GREEN
                mensaje_text.update()
                
                # Actualizar inmediatamente
                show_view(show_murals, kind)
            else:
                mensaje_text.value = "❌ Error al guardar"
                mensaje_text.color = RED
                mensaje_text.update()

        # Botón de frecuencia rápida: alterna 15 / 30 / 60 / 90 / 180 días
        def toggle_frecuencia_rapida(e):
            actual = (frecuencia_field.value or "").strip()
            opciones = ["15", "30", "60", "90", "180"]
            if actual in opciones:
                idx = opciones.index(actual)
                nueva = opciones[(idx + 1) % len(opciones)]
            else:
                nueva = "15"
            frecuencia_field.value = nueva
            frecuencia_field.update()
        
        # Fila con campo de fecha y botón de calendario
        fecha_row = ft.Row([
            fecha_field,
            ft.Container(
                content=ft.Text("📅", size=18),
                on_click=lambda e: setattr(date_picker, "open", True) or page.update(),
                padding=8,
                border_radius=8,
                bgcolor=f"{ACCENT}20",
                width=50,
                height=48,
                tooltip="Seleccionar fecha en calendario",
            ),
        ], alignment="start", spacing=8)

        # Fila con campo de frecuencia y botón de selección rápida (cíclico)
        frecuencia_row = ft.Row([
            frecuencia_field,
            ft.Container(
                content=ft.Text("⚙", size=16),
                on_click=toggle_frecuencia_rapida,
                padding=8,
                border_radius=8,
                bgcolor=f"{ACCENT}20",
                width=50,
                height=48,
                tooltip="Alternar entre 15 / 30 / 60 / 90 / 180 días",
            ),
        ], alignment="start", spacing=8)

        page.add(
            ft.Column([
                fecha_row,
                ft.Container(height=8),
                frecuencia_row,
                ft.Container(height=16),
                ft.Row([
                    create_button("Guardar", guardar, bgcolor=GREEN, height=48),
                    create_button("Reset", reset_campos, bgcolor=SUBTEXT, height=48),
                ], spacing=8),
                ft.Container(height=16),
                ft.Container(
                    mensaje_text,
                    padding=12,
                    bgcolor=f"{ACCENT}15",
                    border_radius=10,
                    border=ft.Border.all(2, ACCENT),
                )
            ], spacing=0)
        )
        
        # Establecer valores después de agregar a la página
        fecha_field.value = fecha_actual
        frecuencia_field.value = frecuencia_actual
        page.update()
    
    # ============ INICIO ============
    # Base de datos inicializada mediante StorageService (sin SQLite)
    try:
        show_view(show_home)
    except Exception as e:
        print(f"Error en show_home: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    ft.run(
        main,
        assets_dir="assets",
        web_renderer=ft.WebRenderer.AUTO,
        route_url_strategy=ft.RouteUrlStrategy.HASH,
    )
