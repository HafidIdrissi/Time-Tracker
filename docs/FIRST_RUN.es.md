# Primera ejecución en Windows

[Leer la guía original en inglés](FIRST_RUN.md)

Esta guía dura aproximadamente cinco minutos con el instalador actual de Windows. Los ejemplos siguientes utilizan datos ficticios. Local Time Tracker no carga la actividad a Internet. Esta guía no afirma que el instalador esté firmado digitalmente.

**Nota:** Esta es una traducción de la documentación. La interfaz de la aplicación sigue estando en inglés.

## 1. Descargar

Abre la [última versión publicada](https://github.com/HafidIdrissi/Time-Tracker/releases/latest) y descarga `LocalTimeTracker-Setup-<version>-x64.exe` junto con `SHA256SUMS.txt`.

Comprobación opcional del checksum en PowerShell, desde la carpeta que contiene ambos archivos:

```powershell
Get-FileHash -Algorithm SHA256 "LocalTimeTracker-Setup-<version>-x64.exe"
```

Compara el hash obtenido con la línea correspondiente de `SHA256SUMS.txt`. Sustituye `<version>` por la versión que aparece en la página de la publicación.

## 2. Iniciar la aplicación

Ejecuta el instalador y después abre **Local Time Tracker**. La etiqueta de estado cambia de **Stopped** a **Starting…** y después a **Running**. La línea de detalles indica que el seguimiento está activo. En un primer inicio normal, no necesitas pulsar **Start tracking**.

La actividad permanece en este equipo, en `%LOCALAPPDATA%\LocalTimeTracker\`. Los títulos de las ventanas pueden incluir nombres de documentos privados, búsquedas o asuntos de correos electrónicos. Durante este primer inicio, no se envía nada a un servidor.

## 3. Observar una muestra inofensiva

Deja en primer plano una ventana con contenido ficticio, como un archivo vacío de Notepad llamado `fictional-note.txt`, y después cambia a otra ventana sin información sensible. En **Dashboard**, **LIVE ACTIVITY** debería mostrar la aplicación en primer plano y su ventana. **RECENT ACTIVITY** añade una fila después de la siguiente muestra.

**Running** significa que el rastreador está tomando muestras. **Stopped** significa que no lo está haciendo. El tiempo de inactividad es algo distinto: significa que el teclado y el ratón han permanecido sin actividad, no que el seguimiento se haya desactivado.

## 4. Consultar Usage analysis

Abre la pestaña **Usage analysis**. **Today** está seleccionado de forma predeterminada. Las tarjetas de resumen, el gráfico y las clasificaciones corresponden al mismo día local. Si todavía no se ha guardado ninguna muestra, el gráfico vacío muestra **No activity during this period**.

## 5. Generar un informe sin conexión

Abre **Reports and data**. Mantén la fecha de hoy en **Date (YYYY-MM-DD)** y pulsa **Generate and open report**. El informe es un archivo HTML que se guarda en la carpeta local de informes. **Open reports folder** abre esa carpeta. El informe no necesita conexión a Internet.

## 6. Detener e iniciar el seguimiento

Pulsa **Stop**. La etiqueta vuelve a **Stopped** y la línea de detalles indica que el seguimiento no está en ejecución. Pulsa **Start tracking** para volver a tomar muestras. Cerrar la ventana también detiene el seguimiento.

No pulses **Reset** ni **Reset all activity history** mientras estás aprendiendo a utilizar la aplicación. Estas acciones eliminan permanentemente los períodos registrados. Los informes HTML generados anteriormente se conservan.

## Si no aparece ninguna actividad

- Comprueba que la etiqueta indique **Running**, y no **Stopped** ni **Error**.
- Haz clic en una ventana normal para ponerla en primer plano y espera a que se registre una muestra.
- Algunas ventanas abiertas con privilegios elevados pueden ocultar su título a una aplicación que no tiene esos privilegios.
- Las visitas muy breves a una ventana pueden ocurrir entre dos muestras y no quedar registradas.

Para obtener más ayuda, consulta [SUPPORT.md](../SUPPORT.md). No envíes tu archivo `activity.db` ni capturas de pantalla que muestren títulos de ventanas reales.