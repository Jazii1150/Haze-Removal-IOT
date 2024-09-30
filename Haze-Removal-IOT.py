import numpy as np
import cv2
import time
from tkinter import Tk, filedialog, Button, Label, Frame, Canvas, Scrollbar, StringVar, messagebox, Toplevel
from PIL import Image, ImageTk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from picamera2 import Picamera2, Preview
from threading import Thread

# Global variables
picam2 = None
stop_streaming = False
label_camera = None

class Node(object):
    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        self.value = value

def getMinChannel(img):
    return np.min(img, axis=2)

def getDarkChannel(img, blockSize=15):
    A = int((blockSize - 1) / 2)
    H = img.shape[0] + blockSize - 1
    W = img.shape[1] + blockSize - 1
    imgMiddle = 255 * np.ones((H, W))
    imgMiddle[A:H-A, A:W-A] = img
    imgDark = np.zeros_like(img, np.uint8)
    for i in range(A, H-A):
        for j in range(A, W-A):
            imgDark[i-A, j-A] = np.min(imgMiddle[i-A:i+A+1, j-A:j+A+1])
    return imgDark

def getAtomsphericLight(darkChannel, img, percent=0.001):
    size = darkChannel.size
    nodes = [Node(i, j, darkChannel[i, j]) for i in range(darkChannel.shape[0]) for j in range(darkChannel.shape[1])]
    nodes = sorted(nodes, key=lambda node: node.value, reverse=True)
    atomsphericLight = 0
    for i in range(int(percent * size)):
        for j in range(3):
            if img[nodes[i].x, nodes[i].y, j] > atomsphericLight:
                atomsphericLight = img[nodes[i].x, nodes[i].y, j]
    return atomsphericLight

def getRecoverScene(img, omega=0.95, t0=0.1, blockSize=15):
    imgGray = getMinChannel(img)
    imgDark = getDarkChannel(imgGray, blockSize)
    atomsphericLight = getAtomsphericLight(imgDark, img)
    imgDark = np.float64(imgDark)
    transmission = 1 - omega * imgDark / atomsphericLight
    transmission[transmission < t0] = t0
    sceneRadiance = np.zeros(img.shape)
    img = np.float64(img)
    for i in range(3):
        sceneRadiance[:, :, i] = (img[:, :, i] - atomsphericLight) / transmission + atomsphericLight
        sceneRadiance[:, :, i][sceneRadiance[:, :, i] > 255] = 255
        sceneRadiance[:, :, i][sceneRadiance[:, :, i] < 0] = 0
    return np.uint8(sceneRadiance)

def calculate_haze_reduction(original_img, dehazed_img):
    original_img = np.float64(original_img)
    dehazed_img = np.float64(dehazed_img)
    
    original_dark_channel = getDarkChannel(getMinChannel(original_img))
    dehazed_dark_channel = getDarkChannel(getMinChannel(dehazed_img))
    
    original_mean_dark = np.mean(original_dark_channel)
    dehazed_mean_dark = np.mean(dehazed_dark_channel)
    
    haze_reduction_percentage = 100 * (original_mean_dark - dehazed_mean_dark) / original_mean_dark
    return max(0, min(100, haze_reduction_percentage))

def save_image_as_txt(image, processing_time, haze_reduction_percentage):
    try:
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            height, width, _ = image.shape
            with open(file_path, 'w') as f:
                f.write(f"Image Size: {width} x {height} pixels\n")
                f.write(f"Processing Time: {processing_time:.2f} seconds\n")
                f.write(f"Haze Reduction: {haze_reduction_percentage:.2f}%\n")
            messagebox.showinfo("Success", "Image and processing details saved as txt file successfully!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def save_image_as_file(image):
    try:
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg;*.jpeg")])
        if file_path:
            if len(image.shape) == 3 and image.shape[2] == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            img_pil = Image.fromarray(image_rgb)
            img_pil.save(file_path)
            messagebox.showinfo("Success", "Image saved successfully!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def load_image():
    file_path = filedialog.askopenfilename()
    if file_path:
        try:
            start_time = time.time()
            
            img = cv2.imread(file_path)
            if img is None:
                raise ValueError("Unable to load image. Please check the file format.")
            img_resized = cv2.resize(img, (320, 240))
            dehazed_img = getRecoverScene(img_resized)
            
            haze_reduction_percentage = calculate_haze_reduction(img_resized, dehazed_img)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            display_images(img_resized, dehazed_img)
            plot_histogram(img_resized, dehazed_img)
            update_image_info(img_resized, processing_time, haze_reduction_percentage)

            root.dehazed_img = dehazed_img
            root.processing_time = processing_time
            root.haze_reduction_percentage = haze_reduction_percentage

        except Exception as e:
            messagebox.showerror("Error", str(e))

def capture_image():
    global picam2, restart_stream_button
    try:
        if not picam2:
            return

        # Stop camera before configuring
        if picam2.started:
            picam2.stop()

        # Configure and start camera
        config = picam2.create_still_configuration(main={"size": (320, 240)})
        picam2.configure(config)
        picam2.start()

        start_time = time.time()
        frame = picam2.capture_array()
        dehazed_img = getRecoverScene(frame)
        haze_reduction_percentage = calculate_haze_reduction(frame, dehazed_img)
        end_time = time.time()
        processing_time = end_time - start_time

        display_images(frame, dehazed_img)
        plot_histogram(frame, dehazed_img)
        update_image_info(frame, processing_time, haze_reduction_percentage)

        root.dehazed_img = dehazed_img
        root.processing_time = processing_time
        root.haze_reduction_percentage = haze_reduction_percentage

        picam2.stop()
        restart_stream_button.config(state="normal")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def display_images(original_img, dehazed_img):
    original_img_rgb = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
    dehazed_img_rgb = cv2.cvtColor(dehazed_img, cv2.COLOR_BGR2RGB)
    
    original_img_pil = Image.fromarray(original_img_rgb)
    dehazed_img_pil = Image.fromarray(dehazed_img_rgb)
    
    original_img_tk = ImageTk.PhotoImage(original_img_pil)
    dehazed_img_tk = ImageTk.PhotoImage(dehazed_img_pil)
    
    label_original.config(image=original_img_tk)
    label_original.image = original_img_tk
    
    label_dehazed.config(image=dehazed_img_tk)
    label_dehazed.image = dehazed_img_tk

def plot_histogram(original_img, dehazed_img):
    for widget in histogram_frame.winfo_children():
        widget.destroy()

    fig = Figure(figsize=(8, 4), dpi=100)
    colors = ['r', 'g', 'b']
    
    ax1 = fig.add_subplot(121)
    ax1.set_title("Original Image Histogram")
    for i, color in enumerate(colors):
        hist = cv2.calcHist([original_img], [i], None, [256], [0, 256])
        ax1.plot(hist, color=color)
    
    ax2 = fig.add_subplot(122)
    ax2.set_title("Dehazed Image Histogram")
    for i, color in enumerate(colors):
        hist = cv2.calcHist([dehazed_img], [i], None, [256], [0, 256])
        ax2.plot(hist, color=color)
    
    canvas = FigureCanvasTkAgg(fig, master=histogram_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)

def update_image_info(img, processing_time, haze_reduction_percentage):
    height, width, _ = img.shape
    info_text.set(f"Image Size: {width} x {height} pixels\nProcessing Time: {processing_time:.2f} seconds\nHaze Reduction: {haze_reduction_percentage:.2f}%")

def close_gui():
    global picam2, stop_streaming
    stop_streaming = True  # Stop streaming before closing
    if picam2:
        picam2.stop()
        picam2.close()
    root.destroy()

def stream_camera():
    global picam2, update_frame_thread, stop_streaming, label_camera, restart_stream_button
    try:
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(main={"size": (320, 240)})
        picam2.configure(config)
        picam2.start()
        stop_streaming = False

        def update_frame():
            while not stop_streaming:
                if label_camera and label_camera.winfo_exists():
                    frame = picam2.capture_array()
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img_pil = Image.fromarray(frame_rgb)
                    img_tk = ImageTk.PhotoImage(img_pil)
                    label_camera.config(image=img_tk)
                    label_camera.image = img_tk
                else:
                    break

        stream_window = Toplevel(root)
        stream_window.title("Camera Stream")

        label_camera = Label(stream_window)
        label_camera.pack()

        btn_capture = Button(stream_window, text="Capture Image", command=capture_image, bg="lightblue", font=("Helvetica", 12, "bold"))
        btn_capture.pack()

        restart_stream_button = Button(stream_window, text="Start Camera", command=restart_camera, state="disabled", bg="lightgreen", font=("Helvetica", 12, "bold"))
        restart_stream_button.pack()

        btn_close = Button(stream_window, text="Close", command=lambda: close_stream(stream_window), bg="red", font=("Helvetica", 12, "bold"))
        btn_close.pack()

        update_frame_thread = Thread(target=update_frame)
        update_frame_thread.daemon = True
        update_frame_thread.start()

        stream_window.protocol("WM_DELETE_WINDOW", lambda: close_stream(stream_window))
    except Exception as e:
        messagebox.showerror("Error", str(e))

def restart_camera():
    global picam2, update_frame_thread, stop_streaming, label_camera
    try:
        if picam2 and not picam2.started:
            picam2.start()
            stop_streaming = False

            def update_frame():
                while not stop_streaming:
                    if label_camera and label_camera.winfo_exists():
                        frame = picam2.capture_array()
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        img_pil = Image.fromarray(frame_rgb)
                        img_tk = ImageTk.PhotoImage(img_pil)
                        label_camera.config(image=img_tk)
                        label_camera.image = img_tk
                    else:
                        break

            update_frame_thread = Thread(target=update_frame)
            update_frame_thread.daemon = True
            update_frame_thread.start()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def close_stream(stream_window):
    global picam2, stop_streaming
    stop_streaming = True  # Stop streaming before closing the window
    if picam2:
        picam2.stop()
        picam2.close()
        picam2 = None
    stream_window.destroy()

# GUI setup code

root = Tk()
root.title("Haze Removal or Density Reduction from Image")
root.geometry("1200x800")
root.configure(bg="#f0f0f0")

canvas_frame = Frame(root, bg="#f0f0f0")
canvas_frame.pack(fill="both", expand=True)

canvas = Canvas(canvas_frame, bg="#f0f0f0")
canvas.pack(side="left", fill="both", expand=True)

vsb = Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
vsb.pack(side="right", fill="y")
hsb = Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
hsb.pack(side="bottom", fill="x")

scrollable_frame = Frame(canvas, bg="#f0f0f0")
scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

canvas.config(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
vsb.config(command=canvas.yview)
hsb.config(command=canvas.xview)

button_frame = Frame(scrollable_frame, bg="#f0f0f0")
button_frame.pack(side="top", fill="x")

button_load = Button(button_frame, text="Load Image", command=load_image, bg="lightblue", font=("Helvetica", 12, "bold"))
button_load.pack(side="left", padx=10, pady=10)

stream_button = Button(button_frame, text="Stream Camera", command=stream_camera, bg="lightgreen", font=("Helvetica", 12, "bold"))
stream_button.pack(side="left", padx=10)

save_image_button = Button(button_frame, text="Save Image", command=lambda: save_image_as_file(root.dehazed_img if hasattr(root, 'dehazed_img') else np.array([])), bg="lightyellow", font=("Helvetica", 12, "bold"))
save_image_button.pack(side="left", padx=10)

save_txt_button = Button(button_frame, text="Save as TXT", command=lambda: save_image_as_txt(root.dehazed_img if hasattr(root, 'dehazed_img') else np.array([]), root.processing_time if hasattr(root, 'processing_time') else 0, root.haze_reduction_percentage if hasattr(root, 'haze_reduction_percentage') else 0), bg="lightcoral", font=("Helvetica", 12, "bold"))
save_txt_button.pack(side="left", padx=10)

button_close = Button(button_frame, text="Close GUI", command=close_gui, bg="red", font=("Helvetica", 12, "bold"))
button_close.pack(side="right", padx=10, pady=10)

image_frame = Frame(scrollable_frame, bg="#f0f0f0")
image_frame.pack(fill="both", expand=True)

label_original = Label(image_frame, bg="#f0f0f0")
label_original.pack(side="left", padx=10, pady=10)

label_dehazed = Label(image_frame, bg="#f0f0f0")
label_dehazed.pack(side="right", padx=10, pady=10)

histogram_frame = Frame(scrollable_frame, bg="#f0f0f0")
histogram_frame.pack(fill="both", expand=True)

info_frame = Frame(scrollable_frame, bg="#f0f0f0")
info_frame.pack(side="bottom", fill="x", pady=10)

info_text = StringVar()
info_label = Label(info_frame, textvariable=info_text, bg="#f0f0f0", font=("Helvetica", 12))
info_label.pack()

root.mainloop()
