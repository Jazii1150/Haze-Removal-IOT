# Use Manual for Haze Removal Web Application
 1. System Requirements
    Python Version 3: You need to have Python installed to run the code.

    Required Libraries:
        numpy: Used for mathematical computations and array processing.
    
        opencv-python: Used for image processing.
    
        Pillow: Used for handling images in various formats.
    
        matplotlib: Used for creating graphs and histograms for images.
    
        picamera2: Used for controlling the camera on the Raspberry Pi.
    
        tkinter: A library for creating graphical user interfaces (GUI).
    
    Raspberry Pi with Camera Module (if you want to use the camera streaming feature):
    
    Picamera2 must be installed on the Raspberry Pi to control the camera module.
    
2. Key Features of the Application

   Image Loading:
   
        You can select an image file from your computer for haze removal.
       This feature will resize the image and process it to remove haze using the Dark Channel Prior technique.

   Camera Streaming (for Raspberry Pi):

        If you have a camera connected to the Raspberry Pi, you can open a live video stream from the camera.
        You can also capture images from the stream and immediately remove haze from the captured images.

    Image Display:

        The application will display the original image and the haze-removed image side by side for comparison.
        You can view the haze-removed image in histogram format to show the color distribution of the image before and after processing.

    Image and Data Saving:

        You can save the haze-removed image as a PNG or JPEG file.
        Additionally, you can save processing details such as image size, processing time, and haze reduction percentage in a TXT file.
3. Usage Instructions

       Open the Application: When you open the GUI application, you will see various buttons for loading images, streaming the camera, saving images, and closing the program.

        Load Image: Press the "Load Image" button to select and open the image you want to remove haze from.

        Stream Camera: Press the "Stream Camera" button to open the live video stream from your Raspberry Pi camera.

        Capture Image from Camera: While streaming, you can press the "Capture Image" button to take a picture and process that image immediately.

        Save Image: Once you have the haze-removed image, you can press the "Save Image" button to save the image to your computer.

        Save Data as TXT: If you want to save processing details, you can press the "Save as TXT" button to save the data in a TXT file.

4. Closing the Program

       Close the Application: If you want to close the program, you can press the "Close GUI" button, which will stop the program and close the application.
   
6. Internal Functionality

       Haze Removal: This program uses a technique called Dark Channel Prior to remove haze from images. It calculates the darkest channel in blocks of the image and adjusts the remaining light from the haze to eliminate it.

        Percentage of Haze Reduction Calculation: The program calculates the average darkness in the image before and after processing to determine how much haze has been reduced.

6. Precautions

       Processing large images or images with high detail may take some time, depending on the resources of your computer or Raspberry Pi.
