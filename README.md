# 🐔 Pio AI — Manual de uso

**Pio AI** es una plataforma de control avícola. Permite contar tus aves y huevos
con ayuda de la **inteligencia artificial**: tomas una foto del corral, la IA cuenta
los animales y tú validas el resultado. Todo queda registrado para llevar el control
de tu granja.

Esta guía explica cómo usar el sistema **paso a paso desde la pantalla** (vista del usuario).

---

## 📑 Índice
1. [Iniciar sesión](#1-iniciar-sesión)
2. [Las secciones del menú](#2-las-secciones-del-menú)
3. [Registrar aves y huevos manualmente](#3-registrar-aves-y-huevos-manualmente)
4. [Contar con la Cámara IA (subir foto)](#4-contar-con-la-cámara-ia-subir-foto)
5. [Ver el historial de aves y huevos](#5-ver-el-historial-de-aves-y-huevos)
6. [Otras secciones](#6-otras-secciones)
7. [Preguntas frecuentes](#7-preguntas-frecuentes)

---

## 1. Iniciar sesión

Para entrar al sistema necesitas una cuenta.

1. Abre la aplicación. Verás la pantalla de **inicio de sesión** (`/login`).
2. Ingresa tu **correo** y tu **contraseña**.
3. Pulsa **"Iniciar sesión"**.

> 🔐 **Importante:** todas las pantallas están protegidas. Si no inicias sesión,
> el sistema te redirige automáticamente al login. No puedes ver ni registrar nada
> sin haber entrado.

**¿No tienes cuenta?** Usa el enlace de **Registro** (`/registro`) para crear un usuario nuevo.

---

## 2. Las secciones del menú

Una vez dentro, en el menú lateral (o la barra inferior en el celular) encuentras:

| Sección | Para qué sirve |
|---|---|
| 🏠 **Inicio** | Pantalla principal / resumen |
| 📋 **Registro** | Ingresar aves y huevos **manualmente** |
| 📷 **Cámara IA** | Tomar/subir una foto para que la **IA cuente** |
| 🕘 **Historial** | Ver todos los registros guardados (aves y huevos) |
| 🔔 **Alertas** | Avisos del sistema (mortalidad, producción, etc.) |
| 👤 **Perfil** | Tus datos de usuario |

---

## 3. Registrar aves y huevos manualmente

En la sección **Registro** (`/registro`) puedes anotar tus animales sin usar la cámara.

1. Verás tres contadores: **Pollitos**, **Gallinas** y **Huevos**.
2. Usa los botones **➕ / ➖** para indicar la cantidad de cada uno.
3. (Opcional) Agrega una **nota** con algún detalle.
4. Pulsa **guardar**.

> 🥚 **Nota sobre huevos:** para registrar huevos primero debe existir al menos
> una ave registrada, porque los huevos se asocian a una gallina. Si no hay aves,
> el sistema te avisará.

---

## 4. Contar con la Cámara IA (subir foto)

Esta es la función principal. Está en la sección **Cámara IA** (`/captura`).

### ¿Qué imagen debo subir?

✅ **Sí funciona:**
- **Fotografías reales** de tu corral, granja o gallinero.
- Gallinas, gallos, pollitos y huevos **de gallina doméstica** reales.
- Buena luz, los animales visibles (no muy lejos ni borrosos).
- Formatos de imagen comunes (**JPG / PNG**), tomadas con el celular o la cámara.

❌ **No funciona (la IA lo rechaza y cuenta 0):**
- Dibujos, caricaturas, emojis, logos o imágenes generadas por computadora.
- Otras aves (patos, pavos, loros, canarios, etc.) o animales que no sean gallinas.
- Fotos de comida (pollo cocido, huevos fritos) o huevos pintados/decorados.
- Imágenes sin aves, muy oscuras o demasiado borrosas.

> 💡 La IA está hecha para ser **precisa**: si tiene dudas, prefiere no contar antes
> que equivocarse. Por eso una foto clara y real da mejores resultados.

### ¿Dónde se sube y cómo?

1. Entra a **Cámara IA**.
2. Elige una de estas opciones:
   - **Cámara del dispositivo** → toma la foto en el momento.
   - **Seleccionar imagen** → eliges una foto de tu galería.
3. Revisa la **vista previa** de la foto.
4. Pulsa **"Analizar con IA"**.

### ¿Qué pasa después?

El sistema hace todo automáticamente:
1. **Optimiza** la imagen (la hace más liviana para subir rápido).
2. La **sube** al servidor (se guarda en la nube).
3. La **IA la analiza** y devuelve el conteo.

Verás el resultado con **contadores separados por tipo**: por ejemplo, "2 gallinas"
y "3 huevos" aparecen en contadores distintos.

### Corregir el conteo (si la IA se equivocó)

Si la IA contó mal, tú puedes corregirlo:
1. Usa los botones **➕ / ➖** de cada tipo para ajustar el número real.
2. (Opcional) Escribe **por qué** se equivocó la IA. Esto sirve para mejorar el modelo.
3. Pulsa **"Confirmar conteo validado"**.

> ✅ Al confirmar, el conteo se **guarda en el historial**. Ese conteo validado es el
> que queda como oficial.

---

## 5. Ver el historial de aves y huevos

Todos los registros guardados (los de la cámara y los manuales) se ven en la sección
**Historial** (`/historial`).

Ahí encuentras:

- **📊 Tarjetas con los totales** arriba: total de Pollitos, Gallinas y Huevos.
- **🔘 Filtros**: botones para ver **Todos / Pollitos / Gallinas / Huevos**.
- **📋 Lista de aves**: cada registro muestra el tipo, la fecha y la cantidad.
- **🥚 Lista de producción de huevos**: cada registro con su fecha y cantidad.

> Aquí es donde revisas la evolución de tu granja: cuántas aves y huevos tienes,
> y cuándo se registraron.

---

## 6. Otras secciones

- **🔔 Alertas** (`/alertas`): muestra avisos del sistema (por ejemplo, baja de
  producción o mortalidad). Puedes marcarlas como leídas.
- **📈 Métricas de IA** (`/ia-metricas`): muestra qué tan precisa fue la IA en los
  últimos análisis (precisión, confianza, tiempo de procesamiento).
- **👤 Perfil** (`/perfil`): tus datos de usuario y la opción de cerrar sesión.

---

## 7. Preguntas frecuentes

**¿Por qué la IA contó 0 si hay gallinas en la foto?**
Probablemente la foto no es clara (oscura, borrosa, lejana) o la IA tuvo dudas.
Toma otra foto con mejor luz y más cerca, y vuelve a intentar.

**¿Puedo corregir el conteo de la IA?**
Sí. En la pantalla de resultado, ajusta con los botones ➕ / ➖ y confirma.
Esa corrección además ayuda a que la IA mejore.

**¿Dónde quedan guardados mis conteos?**
En el **Historial**. Tanto los conteos de la cámara como los registros manuales
aparecen ahí.

**¿Qué formato de imagen uso?**
Fotos reales en **JPG o PNG**, tomadas con el celular o la cámara. El sistema
las optimiza solo, no necesitas hacer nada.

**Se me cerró la sesión, ¿qué hago?**
Vuelve a iniciar sesión con tu correo y contraseña. Por seguridad, la sesión
puede expirar.

---

> Pio AI — *Plataforma de control de los polluelos* 🐥
