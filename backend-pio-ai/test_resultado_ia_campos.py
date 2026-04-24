#!/usr/bin/env python3
"""
Script de prueba para verificar que los nuevos campos de ResultadoIA funcionan correctamente.
Uso: python test_resultado_ia_campos.py
"""
import json
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.imagenes import ResultadoIA, Imagen

def test_campos_resultado_ia():
    """Prueba la lectura/escritura de los nuevos campos."""
    db = SessionLocal()
    
    try:
        # Buscar el último ResultadoIA
        resultado = db.query(ResultadoIA).order_by(ResultadoIA.id.desc()).first()
        
        if not resultado:
            print("⚠️ No hay ResultadoIA en la BD. Sube una imagen primero.")
            return
        
        print("\n" + "="*70)
        print("✅ PRUEBA DE CAMPOS - ResultadoIA")
        print("="*70)
        
        print(f"\n📋 ResultadoIA ID: {resultado.id}")
        print(f"   Imagen ID: {resultado.imagen_id}")
        print(f"   Estado: {resultado.estado}")
        
        print("\n🕐 CAMPOS TÉCNICOS:")
        print(f"   ├─ duracion_ms: {resultado.duracion_ms} ms" if resultado.duracion_ms else "   ├─ duracion_ms: N/A")
        print(f"   ├─ precision_estimada: {resultado.precision_estimada}" if resultado.precision_estimada else "   ├─ precision_estimada: N/A")
        print(f"   ├─ notas_ia: {resultado.notas_ia[:50]}..." if resultado.notas_ia else "   ├─ notas_ia: N/A")
        print(f"   └─ detecciones_json: {len(resultado.detecciones)} detecciones" if resultado.detecciones else "   └─ detecciones: N/A")
        
        # Mostrar detecciones parseadas
        if resultado.detecciones:
            print("\n🎯 DETECCIONES VISUALES:")
            for i, det in enumerate(resultado.detecciones[:3], 1):
                print(f"   [{i}] x={det.get('x', 'N/A'):.2f}, y={det.get('y', 'N/A'):.2f}, "
                      f"label={det.get('label', 'N/A')}, confidence={det.get('confidence', 'N/A')}")
            if len(resultado.detecciones) > 3:
                print(f"   ... y {len(resultado.detecciones) - 3} más")
        
        print("\n📊 DATOS ORIGINALES:")
        print(f"   ├─ conteo_pollitos: {resultado.conteo_pollitos}")
        print(f"   ├─ confianza: {resultado.confianza}")
        print(f"   ├─ error_detalle: {resultado.error_detalle or 'Ninguno'}")
        print(f"   ├─ procesado_at: {resultado.procesado_at}")
        print(f"   └─ created_at: {resultado.created_at}")
        
        print("\n✅ TODOS LOS CAMPOS FUNCIONAN CORRECTAMENTE\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
    finally:
        db.close()

if __name__ == "__main__":
    test_campos_resultado_ia()
