# -- coding: utf-8 --
"""
Procesamiento automático de tapers por carpeta.
Para cada imagen:
 - Ejecuta Canny, extrae perfiles, suaviza, reconoce regiones.
 - Guarda PNGs de depuración y resultados.
 - Guarda .txt con métricas.
 - Agrega fila a un resumen maestro CSV.

Requisitos: numpy, matplotlib, scipy, opencv-python
"""

import os
import csv
import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter, find_peaks

# =========================
# === PARÁMETROS GLOBALES ===
# =========================

# Carpeta con imágenes a procesar (CAMBIA ESTO)
input_dir  = r"C:\Users\tangi\OneDrive\Documentos\UNT\TESIS II\DESARROLLO\AUTOMATIZAR\caracterizar"      # <- pon tu carpeta
output_dir = r"C:\Users\tangi\OneDrive\Documentos\UNT\TESIS II\DESARROLLO\AUTOMATIZAR\caracterizar_V5"        # <- carpeta de salida
os.makedirs(output_dir, exist_ok=True)

# Calibración (pixeles por diámetro) y escalas
calibracion = 15.15 # calibración para caracterizacion 
# 16.7 # calibración para validación   
# #14.35  # número de píxeles en un diámetro calibración pruebas
length_real_um = (640 / calibracion) * 1000  # ancho imagen (640 px) -> µm
height_real_um = (480 / calibracion) * 1000  # alto  imagen (480 px) -> µm

# Parámetros de suavizado y extracción
SMOOTH_WINDOW_FACTOR = 0.09
SMOOTH_POLYORDER = 3

# Canny
GAUSSIAN_BLUR_KERNEL = (1, 1)
CANNY_LOW_THRESHOLD  = 50
CANNY_HIGH_THRESHOLD = 150

# Relleno de huecos y límite de saltos
MAX_GAP_FILL   = 50
MAX_PIXEL_JUMP = 10

# Detección de regiones
TAPER_ANGLE_THRESHOLD_FACTOR = 0.03
WAIST_ANGLE_THRESHOLD_FACTOR = 0.003

# Factor pico por ancho
factor = 0.08
# V1 = 0.1
# V2 = 0.05
# V3 = 0.01
# V4 = 0.2
# V5 = 0.08

# =========================
# === FUNCIONES BASE     ===
# =========================

def process_image_with_canny(image_path, save_path_edges_png=None):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"No se pudo cargar la imagen: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(gray, GAUSSIAN_BLUR_KERNEL, 0)

    mediana = np.median(blurred)
    lower = int(max(0, 0.66 * mediana))
    upper = int(min(255, 1.33 * mediana))

    edges = cv2.Canny(blurred, lower, upper)

    if save_path_edges_png:
        plt.figure(figsize=(8, 4))
        plt.imshow(edges, cmap='gray')
        plt.title(f"Bordes Canny - {os.path.basename(image_path)}")
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(save_path_edges_png, dpi=200)
        plt.close()

    return edges

def fill_gaps_in_profile(profile_px, max_gap=100):
    x_indices = np.arange(len(profile_px))
    interp_profile = np.copy(profile_px)
    nan_mask = np.isnan(profile_px)

    # Extremos
    first_valid_idx = np.flatnonzero(~nan_mask)
    if len(first_valid_idx) > 0 and nan_mask[0]:
        first_valid_val = profile_px[first_valid_idx[0]]
        interp_profile[:first_valid_idx[0]] = first_valid_val

    last_valid_idx = np.flatnonzero(~nan_mask)
    if len(last_valid_idx) > 0 and nan_mask[-1]:
        last_valid_val = profile_px[last_valid_idx[-1]]
        interp_profile[last_valid_idx[-1] + 1:] = last_valid_val

    # Re-eval
    nan_mask = np.isnan(interp_profile)
    nan_diff = np.diff(nan_mask.astype(int))
    nan_starts = np.where(nan_diff == 1)[0] + 1
    nan_ends   = np.where(nan_diff == -1)[0]

    if nan_mask[0] and (len(nan_starts) == 0 or nan_starts[0] != 0):
        nan_starts = np.insert(nan_starts, 0, 0)
    if nan_mask[-1] and (len(nan_ends) == 0 or nan_ends[-1] != len(interp_profile) - 1):
        nan_ends = np.append(nan_ends, len(interp_profile) - 1)


    if len(nan_starts) > len(nan_ends):
        nan_ends = np.append(nan_ends, len(interp_profile) - 1)
    elif len(nan_ends) > len(nan_starts):
        nan_starts = np.insert(nan_starts, 0, 0)

    for start, end in zip(nan_starts, nan_ends):
        gap_length = end - start + 1

        # Look for the closest valid points to anchor the interpolation
        # Find index of previous valid point
        prev_valid_idx = np.where(~np.isnan(interp_profile[:start]))[0]
        prev_valid_idx = prev_valid_idx[-1] if len(prev_valid_idx) > 0 else -1

        # Find index of next valid point
        next_valid_idx = np.where(~np.isnan(interp_profile[end+1:]))[0] + end + 1
        next_valid_idx = next_valid_idx[0] if len(next_valid_idx) > 0 else -1

        # Perform interpolation only if both valid points exist and gap is within max_gap
        if prev_valid_idx != -1 and next_valid_idx != -1 and gap_length <= max_gap:
            interp_profile[start:end+1] = np.interp(x_indices[start:end+1],
                                                     [x_indices[prev_valid_idx], x_indices[next_valid_idx]],
                                                     [interp_profile[prev_valid_idx], interp_profile[next_valid_idx]])
        # If no valid points for interpolation, keep as NaN (or fill with a default value if needed)
        # For now, if not interpolated, they remain as is. Savitzky-Golay will later require non-NaNs.

    return interp_profile

def extract_fiber_edges(edges_img, max_pixel_jump=20):
    height, width = edges_img.shape
    y_upper_px = np.full(width, np.nan)
    y_lower_px = np.full(width, np.nan)

    last_valid_upper = np.nan
    last_valid_lower = np.nan

    for x in range(width):
        current_upper = np.nan
        current_lower = np.nan

        for y in range(height):
            if edges_img[y, x] > 0:
                current_upper = y
                break

        for y in range(height - 1, -1, -1):
            if edges_img[y, x] > 0:
                current_lower = y
                break

        if not np.isnan(current_upper):
            if np.isnan(last_valid_upper): # Si es el primer punto válido
                y_upper_px[x] = current_upper
                last_valid_upper = current_upper
            elif abs(current_upper - last_valid_upper) <= max_pixel_jump:
                y_upper_px[x] = current_upper
                last_valid_upper = current_upper
            else: # El salto es demasiado grande, ignorar este punto
                y_upper_px[x] = np.nan # Deja un NaN para que fill_gaps lo maneje
        else:
            y_upper_px[x] = np.nan # Si no se encontró un borde, dejar NaN

        # Para el borde inferior
        if not np.isnan(current_lower):
            if np.isnan(last_valid_lower): # Si es el primer punto válido
                y_lower_px[x] = current_lower
                last_valid_lower = current_lower
            elif abs(current_lower - last_valid_lower) <= max_pixel_jump:
                y_lower_px[x] = current_lower
                last_valid_lower = current_lower
            else: # El salto es demasiado grande, ignorar este punto
                y_lower_px[x] = np.nan # Deja un NaN para que fill_gaps lo maneje
        else:
            y_lower_px[x] = np.nan # Si no se encontró un borde, dejar NaN


    y_upper_px_filtered = fill_gaps_in_profile(y_upper_px, max_gap=MAX_GAP_FILL)
    y_lower_px_filtered = fill_gaps_in_profile(y_lower_px, max_gap=MAX_GAP_FILL)

    return y_upper_px_filtered, y_lower_px_filtered

def suavizar_perfiles_individuales(y_upper_px, y_lower_px, window_length_factor=0.05, polyorder=3):
    N = len(y_upper_px)
    wl = int(N * window_length_factor)
    if wl % 2 == 0: wl += 1
    if wl < 3: wl = 3
    if wl >= N: wl = N - 1 if N % 2 == 0 else N
    if wl < 3: wl = 3

    y_upper_smooth = savgol_filter(y_upper_px, wl, polyorder)
    y_lower_smooth = savgol_filter(y_lower_px, wl, polyorder)
    
    return y_upper_smooth, y_lower_smooth

def longitud_taper_por_picos_ancho(x_coords, y_upper_coords, y_lower_coords,
                                   window_length_factor=0.05, polyorder=3, plot_debug=False, debug_path=False):
    x = np.asarray(x_coords, dtype=float)
    y_upper = np.asarray(y_upper_coords, dtype=float)
    y_lower = np.asarray(y_lower_coords, dtype=float)
    width = y_upper - y_lower

    N = len(width)
    if N < 5:
        return float(x[-1] - x[0]), float(x[0]), float(x[-1])

    wl = int(max(3, round(N * window_length_factor)))
    if wl % 2 == 0: 
        wl += 1
    wl = min(wl, N - 1)
    width_smooth = savgol_filter(width, wl, min(polyorder, wl - 1))

    peaks, props = find_peaks(-width_smooth,
                              distance=max(5, N // 10),
                              prominence=np.ptp(width_smooth) * factor)

    if len(peaks) < 2:
        i_left  = np.argmin(width_smooth[:N//2])
        i_right = np.argmin(width_smooth[N//2:]) + N//2
    else:
        # Tomar los dos valles más separados entre sí
        # (desempate: profundidad)
        order = np.argsort(width_smooth[peaks])  # menor ancho = más valle
        i1 = peaks[order[0]]
        i2 = max(peaks[order[1:]], key=lambda i: abs(i - i1))
        i_left, i_right = sorted([i1, i2])

    x_left = float(x[i_left])
    x_right = float(x[i_right])
    L = float(x_right - x_left)

    if plot_debug and debug_path:
        plt.figure(figsize=(8, 4))
        plt.plot(x, width, label="Perfil de ancho (sin suavizar)", alpha=0.4)
        plt.plot(x, width_smooth, label="Perfil de ancho suavizado", linewidth=2)
        if len(peaks) > 0:
            plt.scatter(x[peaks], width_smooth[peaks], zorder=5, label="Valles detectados")
        plt.axvline(x_left,  linestyle='--', label='Valle Izquierdo')
        plt.axvline(x_right, linestyle='--', label='Valle Derecho')
        plt.title("Detección de valles (mínimos de diámetro)")
        plt.xlabel("Posición X [µm]")
        plt.ylabel("Diámetro [µm]")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(debug_path, dpi=200)
        plt.close()

    return L, x_left, x_right

def pixel_to_microns(x_pixels, y_pixels, scale_x_um_per_pixel, scale_y_um_per_pixel):
    x_um = np.array(x_pixels) * scale_x_um_per_pixel
    y_um = np.array(y_pixels) * scale_y_um_per_pixel
    return x_um, y_um

def recognize_fiber_taper(x_coords, y_upper_coords, y_lower_coords,
                          taper_angle_threshold_factor=0.03,
                          waist_angle_threshold_factor=0.005,
                          width_tolerance_factor=0.05):
    widths = np.abs(y_upper_coords - y_lower_coords)

    window_length_width_smooth = min(len(widths) // 5, 51)
    if window_length_width_smooth % 2 == 0: window_length_width_smooth += 1
    if window_length_width_smooth < 3: window_length_width_smooth = 3

    smoothed_widths = savgol_filter(widths, window_length=window_length_width_smooth, polyorder=3)

    min_width_idx = np.argmin(smoothed_widths)
    min_width_value = smoothed_widths[min_width_idx]
    x_at_min_width = x_coords[min_width_idx]

    sorted_widths = np.sort(smoothed_widths)
    idx_90 = int(len(sorted_widths) * 0.90)
    nominal_width = np.mean(sorted_widths[idx_90:])
    
    if nominal_width < min_width_value:
        nominal_width = smoothed_widths[0]
    if nominal_width == 0:
        nominal_width = 1

    width_gradients = np.gradient(smoothed_widths, x_coords)
    abs_gradients = np.abs(width_gradients)

    max_gradient_value = np.max(abs_gradients)
    taper_angle_threshold = max_gradient_value * taper_angle_threshold_factor

    left_taper_start_idx = 0
    for i in range(1, min_width_idx + 1):
        if abs_gradients[i] > taper_angle_threshold and smoothed_widths[i] < nominal_width * (1 - width_tolerance_factor/2):
            left_taper_start_idx = i
            break

    right_taper_end_idx = len(x_coords) - 1
    for i in range(len(x_coords) - 2, min_width_idx - 1, -1):
        if abs_gradients[i] > taper_angle_threshold and smoothed_widths[i] < nominal_width * (1 - width_tolerance_factor/2):
            right_taper_end_idx = i
            break
        
    # Ajuste para casos donde los inicios/fines de taper están muy cerca del mínimo
    if abs(x_coords[left_taper_start_idx] - x_at_min_width) < (nominal_width * 0.1) and left_taper_start_idx > 0:
        for i in range(min_width_idx, -1, -1):
            if smoothed_widths[i] > nominal_width * (1 - width_tolerance_factor):
                left_taper_start_idx = i
                break

    if abs(x_coords[right_taper_end_idx] - x_at_min_width) < (nominal_width * 0.1) and right_taper_end_idx < len(x_coords) - 1:
        for i in range(min_width_idx, len(x_coords)):
            if smoothed_widths[i] > nominal_width * (1 - width_tolerance_factor):
                right_taper_end_idx = i
                break

    if left_taper_start_idx >= right_taper_end_idx:
        left_taper_start_idx = 0
        right_taper_end_idx = len(x_coords) - 1

    x_taper_start = x_coords[left_taper_start_idx]
    x_taper_end   = x_coords[right_taper_end_idx]
    taper_length  = x_taper_end - x_taper_start

    waist_abs_gradient_threshold = max_gradient_value * waist_angle_threshold_factor
    if waist_abs_gradient_threshold < 1e-6: # Evitar umbral muy pequeño
        waist_abs_gradient_threshold = 1e-6

    waist_start_idx = min_width_idx
    for i in range(min_width_idx, -1, -1):
        if abs_gradients[i] <= waist_abs_gradient_threshold:
            waist_start_idx = i
        else:
            break

    waist_end_idx = min_width_idx
    for i in range(min_width_idx, len(x_coords)):
        if abs_gradients[i] <= waist_abs_gradient_threshold:
            waist_end_idx = i
        else:
            break

    if waist_end_idx < waist_start_idx: # Si la detección falla o la cintura es muy corta
        waist_start_idx = min_width_idx
        waist_end_idx = min_width_idx

    x_waist_start = x_coords[waist_start_idx]
    x_waist_end = x_coords[waist_end_idx]
    longitud_cintura = x_waist_end - x_waist_start

    # Ajuste final si la cintura es casi un punto
    if longitud_cintura < (x_coords[1] - x_coords[0]) * 2 and len(x_coords) > 1: # Si es menor a 2 píxeles de longitud
        longitud_cintura = (x_coords[1] - x_coords[0]) * 2
        x_waist_start = x_at_min_width - longitud_cintura / 2
        x_waist_end = x_at_min_width + longitud_cintura / 2

    # --- NUEVO: Longitud de taper por picos del perfil superior ---
        L_picos, x_pico_izq, x_pico_der = longitud_taper_por_picos_ancho(
        x_coords, y_upper_coords, y_lower_coords, plot_debug=True
    )

    return {
        "ancho_nominal": nominal_width,
        "ancho_minimo_waist": min_width_value,
        "x_waist": x_at_min_width,
        "longitud_taper": taper_length,
        "x_inicio_taper": x_taper_start,
        "x_fin_taper": x_taper_end,
        "longitud_cintura": longitud_cintura,
        "x_inicio_cintura": x_waist_start,
        "x_fin_cintura": x_waist_end,
        "perfil_ancho_suavizado": smoothed_widths,
        "pendientes_ancho_suavizadas": width_gradients,
        "taper_angle_threshold": taper_angle_threshold,
        "waist_abs_gradient_threshold": waist_abs_gradient_threshold,
        "longitud_taper_por_picos": L_picos,
        "x_pico_izquierdo": x_pico_izq,
        "x_pico_derecho": x_pico_der
    }

def plot_and_save_profiles(basepath_png, x_data, y_upper, y_lower, taper_info):
    # Perfil completo del ancho + regiones
    fig1 = plt.figure(figsize=(12, 7))
    ax1 = fig1.add_subplot(2,1,1)
    ax1.plot(x_data, taper_info['perfil_ancho_suavizado'], label='Ancho Suavizado', linewidth=2)
    ax1.axhline(taper_info['ancho_nominal'], linestyle='--', label='Ancho Nominal')
    ax1.axvline(taper_info['x_waist'], linestyle=':', label='Waist (min)')
    ax1.axvline(taper_info['x_inicio_taper'], linestyle='--', label='Inicio Taper')
    ax1.axvline(taper_info['x_fin_taper'], linestyle='--', label='Fin Taper')
    ax1.axvline(taper_info['x_inicio_cintura'], label='Inicio Cintura')
    ax1.axvline(taper_info['x_fin_cintura'], label='Fin Cintura')
    ax1.axvline(taper_info['x_pico_izquierdo'], linestyle='-.', label='Valle Izq.')
    ax1.axvline(taper_info['x_pico_derecho'], linestyle='-.', label='Valle Der.')
    ax1.set_title("Ancho de la Fibra (con regiones)")
    ax1.set_xlabel("X [µm]"); ax1.set_ylabel("Ancho [µm]")
    ax1.grid(True, linestyle=':')
    ax1.legend(loc='upper right')
    ax1.set_ylim(bottom=0)

    ax2 = fig1.add_subplot(2,1,2)
    ax2.plot(x_data, taper_info['pendientes_ancho_suavizadas'], linewidth=1, label='Pendiente del Ancho')
    ax2.axhline(0, linestyle='--', linewidth=0.8, color='gray')
    ax2.axhline(taper_info['waist_abs_gradient_threshold'], linestyle=':', label='Umbral Cintura (+)')
    ax2.axhline(-taper_info['waist_abs_gradient_threshold'], linestyle=':', label='Umbral Cintura (-)')
    ax2.axhline(taper_info['taper_angle_threshold'], linestyle=':', label='Umbral Taper (+)')
    ax2.axhline(-taper_info['taper_angle_threshold'], linestyle=':', label='Umbral Taper (-)')
    ax2.set_title("Pendiente del Ancho")
    ax2.set_xlabel("X [µm]"); ax2.set_ylabel("d(Ancho)/dX")
    ax2.grid(True, linestyle=':')
    ax2.legend(loc='center left')
    fig1.tight_layout()
    fig1.savefig(basepath_png + "_ancho_gradiente.png", dpi=200)
    plt.close(fig1)

    # Perfil RAW y suavizado
    fig2 = plt.figure(figsize=(10, 4))
    plt.plot(x_data, y_upper, label='Borde Superior (µm)')
    plt.plot(x_data, y_lower, label='Borde Inferior (µm)')
    plt.fill_between(x_data, y_lower, y_upper, alpha=0.3, label='Cuerpo')
    plt.title("Perfiles (µm) – centrados en línea media")
    plt.xlabel("X [µm]"); plt.ylabel("Y [µm]")
    plt.grid(True, linestyle=':')
    plt.legend()
    plt.tight_layout()
    fig2.savefig(basepath_png + "_perfil_suavizado.png", dpi=200)
    plt.close(fig2)

def save_text_metrics(txt_path, image_name, info):
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"Imagen: {image_name}\n")
        f.write(f"Ancho nominal: {info['ancho_nominal']:.4f} µm\n")
        f.write(f"Ancho mínimo (waist): {info['ancho_minimo_waist']:.4f} µm\n")
        f.write(f"X del waist: {info['x_waist']:.4f} µm\n")
        f.write(f"Longitud región cónica (gradientes): {info['longitud_taper']:.4f} µm\n")
        f.write(f"Inicio cónica X: {info['x_inicio_taper']:.4f} µm\n")
        f.write(f"Fin cónica X: {info['x_fin_taper']:.4f} µm\n")
        f.write(f"Longitud cintura: {info['longitud_cintura']:.4f} µm\n")
        f.write(f"Inicio cintura X: {info['x_inicio_cintura']:.4f} µm\n")
        f.write(f"Fin cintura X: {info['x_fin_cintura']:.4f} µm\n")
        f.write(f"Longitud taper (por valles del ancho): {info['longitud_taper_por_picos']:.4f} µm\n")
        f.write(f"Valle izq X: {info['x_pico_izquierdo']:.4f} µm\n")
        f.write(f"Valle der X: {info['x_pico_derecho']:.4f} µm\n")

# =========================
# === PIPELINE POR IMAGEN ===
# =========================

def process_single_image(image_path):
    img_name = os.path.splitext(os.path.basename(image_path))[0]
    basepath = os.path.join(output_dir, img_name)

    # 1) Canny (guardar PNG)
    edges_png = basepath + "_canny.png"
    edges_img = process_image_with_canny(image_path, save_path_edges_png=edges_png)
    img_h, img_w = edges_img.shape

    # 2) Perfiles en píxeles
    y_upper_px_raw, y_lower_px_raw = extract_fiber_edges(edges_img, max_pixel_jump=MAX_PIXEL_JUMP)

    # 3) Visual RAW perfiles (píxeles)
    fig = plt.figure(figsize=(10, 4))
    x_pixels = np.arange(img_w)
    plt.plot(x_pixels, y_upper_px_raw, 'b-', label='Borde Superior (RAW)')
    plt.plot(x_pixels, y_lower_px_raw, 'r-', label='Borde Inferior (RAW)')
    plt.title(f"Perfil de Píxeles (RAW) - {img_name}")
    plt.xlabel("X [px]"); plt.ylabel("Y [px]")
    plt.grid(True, linestyle=':')
    plt.legend()
    plt.tight_layout()
    fig.savefig(basepath + "_perfil_raw_px.png", dpi=200)
    plt.close(fig)

    # 4) Suavizado
    y_upper_px_smooth, y_lower_px_smooth = suavizar_perfiles_individuales(
        y_upper_px_raw, y_lower_px_raw,
        window_length_factor=SMOOTH_WINDOW_FACTOR,
        polyorder=SMOOTH_POLYORDER
    )
    
    # --- Visualización del perfil suavizado (Individual) ---
    fig_s = plt.figure(figsize=(10, 4))
    plt.plot(x_pixels, y_upper_px_smooth, 'b-', label='Borde Superior (Suavizado)')
    plt.plot(x_pixels, y_lower_px_smooth, 'r-', label='Borde Inferior (Suavizado)')
    plt.title(f"Perfil de Píxeles (Suavizado Individual) - {img_name}")
    plt.xlabel("Píxeles X")
    plt.ylabel("Píxeles Y")
    plt.grid(True, linestyle=':')
    plt.legend()
    plt.tight_layout()
    fig_s.savefig(basepath + "_perfil_suav_px.png", dpi=200)
    plt.close(fig_s)


    # 5) Escala a µm y centrado
    scale_x_um_per_pixel = length_real_um / img_w
    scale_y_um_per_pixel = height_real_um / img_h

    x_pixels = np.arange(img_w)
    x_um, y_upper_um = pixel_to_microns(x_pixels, y_upper_px_smooth, scale_x_um_per_pixel, scale_y_um_per_pixel)
    _,    y_lower_um = pixel_to_microns(x_pixels, y_lower_px_smooth, scale_x_um_per_pixel, scale_y_um_per_pixel)

    centerline = (y_upper_um + y_lower_um) / 2
    y_upper_centered = y_upper_um - centerline
    y_lower_centered = y_lower_um - centerline

    # 6) Reconocer regiones
    info = recognize_fiber_taper(
        x_um, y_upper_centered, y_lower_centered,
        taper_angle_threshold_factor=TAPER_ANGLE_THRESHOLD_FACTOR,
        waist_angle_threshold_factor=WAIST_ANGLE_THRESHOLD_FACTOR
    )

    # 7) Gráficas finales
    plot_and_save_profiles(basepath, x_um, y_upper_centered, y_lower_centered, info)

    # 8) .txt con métricas
    save_text_metrics(basepath + "_resultados.txt", img_name, info)

    # 9) Extra (opcional): depuración de valles
    longitud_taper_por_picos_ancho(
        x_um, y_upper_centered, y_lower_centered,
        window_length_factor=0.05, polyorder=3,
        plot_debug=True, debug_path=basepath + "_valles_ancho.png"
    )

    # 10) Devolver fila para resumen CSV
    return {
        "imagen": img_name,
        "ancho_nominal_um": info['ancho_nominal'],
        "ancho_min_waist_um": info['ancho_minimo_waist'],
        "x_waist_um": info['x_waist'],
        "long_taper_grad_um": info['longitud_taper'],
        "x_ini_taper_um": info['x_inicio_taper'],
        "x_fin_taper_um": info['x_fin_taper'],
        "long_cintura_um": info['longitud_cintura'],
        "x_ini_cintura_um": info['x_inicio_cintura'],
        "x_fin_cintura_um": info['x_fin_cintura'],
        "long_taper_valles_um": info['longitud_taper_por_picos'],
        "x_valle_izq_um": info['x_pico_izquierdo'],
        "x_valle_der_um": info['x_pico_derecho'],
    }

# =========================
# === MAIN: LOTE CARPETA ===
# =========================

def is_image_file(fname):
    ext = os.path.splitext(fname)[1].lower()
    return ext in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

def main():
    files = [f for f in os.listdir(input_dir) if is_image_file(f)]
    files.sort()
    if not files:
        print("No se encontraron imágenes en:", input_dir)
        return

    resumen_csv = os.path.join(output_dir, "resumen_resultados.csv")
    write_header = not os.path.exists(resumen_csv)

    with open(resumen_csv, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            "imagen",
            "ancho_nominal_um", "ancho_min_waist_um", "x_waist_um",
            "long_taper_grad_um", "x_ini_taper_um", "x_fin_taper_um",
            "long_cintura_um", "x_ini_cintura_um", "x_fin_cintura_um",
            "long_taper_valles_um", "x_valle_izq_um", "x_valle_der_um"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        for fname in files:
            path = os.path.join(input_dir, fname)
            print(f"\n=== Procesando: {fname} ===")
            try:
                row = process_single_image(path)
                writer.writerow(row)

                # También imprime a terminal un resumen corto
                print(f"  - Ancho nominal: {row['ancho_nominal_um']:.2f} µm")
                print(f"  - Waist min: {row['ancho_min_waist_um']:.2f} µm en X={row['x_waist_um']:.2f} µm")
                print(f"  - Long taper (grad): {row['long_taper_grad_um']:.2f} µm")
                print(f"  - Long cintura: {row['long_cintura_um']:.2f} µm")
                print(f"  - Long taper (valles): {row['long_taper_valles_um']:.2f} µm")

            except FileNotFoundError as e:
                print("  * Error:", e)
            except Exception as e:
                print("  * Error inesperado:", e)

    print("\nListo. Revisa la carpeta de salida:", output_dir)
    print("Resumen maestro CSV:", resumen_csv)

if __name__ == "__main__":
    main()
