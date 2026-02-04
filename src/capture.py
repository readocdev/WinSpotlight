import dxcam
import numpy as np
from typing import Optional

class CameraManager:
    """
    Manages screen capture using the DXCAM lib.
    Desktop Duplication API access.
    """
    def __init__(self) -> None:
        """Initialize the DXCAM instance with RGB output."""
        try:
            self.camera = dxcam.create(output_color="RGB")
        except Exception as e:
            print(f"[CameraManger] Initialization failed: {e}")
            self.camera = None
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Captures a single frame from the screen.
        Returns:
            np.ndarray: the captured frame if successful.
            None: if the frame could not be grabbed.
        """
        if self.camera is None:
            return None

        # grab() might return None if the screen hasn't changed or is locked
        return self.camera.grab()

    def restarst(self) -> None:
        """
        Reinitializes the camera instance.
        Useful when changing screen resolution or display settings.
        """
        self.stop()
        
        try:
            self.camera = dxcam.create(output_color="RGB")
        except Exception as e:
            print(f"[CameraManager] Restart failed: {e}")
            self.camera = None
    
    def stop(self) -> None:
        """Safely releases the camera resources."""
        if hasattr(self, "camera") and self.camera is not None:
            del self.camera
            self.camera = None
    
    def __del__(self) -> None:
        """Destructor to ensure resources are released."""
        self.stop()


