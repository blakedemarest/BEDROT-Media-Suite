# -*- coding: utf-8 -*-
"""
Image Processing Module for Random Slideshow Generator.

Provides functionality for:
- Scaling and cropping images for different aspect ratios
- PIL compatibility handling
- Image format validation
"""

from PIL import Image


# Patch PIL for compatibility (if needed)
# Check if ANTIALIAS attribute exists, if not, assign LANCZOS from Resampling
if not hasattr(Image, "ANTIALIAS"):
    # Modern PIL uses Resampling enum
    if hasattr(Image, "Resampling") and hasattr(Image.Resampling, "LANCZOS"):
        Image.ANTIALIAS = Image.Resampling.LANCZOS
    else:
        # Fallback if even Resampling is somehow missing (very unlikely)
        # You might need to install a specific Pillow version if this happens
        print("Warning: Could not find appropriate ANTIALIAS/LANCZOS resampling filter in PIL/Pillow.")
        # Assign a default or handle the error appropriately
        # For now, we'll let it potentially fail later if ANTIALIAS is strictly needed
        pass # Or assign a default like Image.BILINEAR if available


class ImageProcessor:
    """
    Handles image processing operations for slideshow generation.
    """
    
    @staticmethod
    def scale_and_crop_to_portrait(image_path, target_w=1632, target_h=2912):
        """
        Open the given image, scale it so the final height matches target_h,
        and then center-crop (or letterbox width) to target_w.
        Returns a PIL Image object (RGB) of size target_w x target_h.
        """
        scaled_img = None
        try:
            # Open image with context manager so the OS handle is released immediately
            with Image.open(image_path) as original_image:
                working_image = original_image.convert("RGB")  # Ensure 3-channel RGB
                orig_w, orig_h = working_image.size

                if orig_h == 0:  # Avoid division by zero
                    raise ValueError(f"Image has zero height: {image_path}")

                # 1) Scale so the final height matches target_h
                scale_factor = target_h / orig_h
                new_w = int(orig_w * scale_factor)
                new_h = target_h  # exactly target_h

                # Use LANCZOS for resizing (handle potential PIL version differences)
                resample_filter = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.ANTIALIAS
                scaled_img = working_image.resize((new_w, new_h), resample_filter)

                # 2) Center-crop horizontally if needed
                if new_w >= target_w:
                    # Crop to target_w wide
                    left = (new_w - target_w) // 2
                    right = left + target_w
                    final_img = scaled_img.crop((left, 0, right, new_h))
                else:
                    # If the scaled width is too small, letterbox
                    final_img = Image.new("RGB", (target_w, target_h), "black")
                    x_offset = (target_w - new_w) // 2
                    final_img.paste(scaled_img, (x_offset, 0))

                # Ensure resulting image data is loaded before leaving context
                final_img.load()
                return final_img
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            # Return a black placeholder image on error
            return Image.new("RGB", (target_w, target_h), "black")
    
    @staticmethod
    def get_target_dimensions(aspect_ratio):
        """
        Get target dimensions based on aspect ratio.
        
        Args:
            aspect_ratio: "9:16" or "16:9"
            
        Returns:
            tuple: (width, height, processing_mode)
        """
        if aspect_ratio == "9:16":
            return 1632, 2912, "scale_crop"
        elif aspect_ratio == "16:9":
            return 2912, 1632, "letterbox"
        else:
            raise ValueError(f"Invalid aspect ratio: {aspect_ratio}")
    
    @staticmethod
    def is_valid_image_extension(file_path):
        """
        Check if the file has a valid image extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if the file has a valid image extension
        """
        import os
        valid_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in valid_extensions
    
    @staticmethod
    def is_valid_image_file(file_path):
        """
        Check if the file is a valid, non-empty image file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if the file is valid and non-empty
        """
        import os
        return (ImageProcessor.is_valid_image_extension(file_path) and 
                os.path.exists(file_path) and 
                os.path.getsize(file_path) > 0)
