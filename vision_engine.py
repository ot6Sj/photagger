import cv2
from PIL import Image

try:
    import torch
    from torchvision import models, transforms
    TORCH_AVAILABLE = True
except Exception as e:
    print(f"Warning: PyTorch could not be loaded ({e}). Deep Learning tagging is disabled.")
    TORCH_AVAILABLE = False


class VisionEngine:
    def __init__(self, blur_threshold=100.0):
        self.blur_threshold = blur_threshold
        self.torch_available = TORCH_AVAILABLE
        self.model = None
        
        if self.torch_available:
            try:
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                self.model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
                self.model = self.model.to(self.device)
                self.model.eval()
                
                self.preprocess = transforms.Compose([
                    transforms.Resize(256),
                    transforms.CenterCrop(224),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225]
                    )
                ])
                self.categories = models.ResNet50_Weights.DEFAULT.meta["categories"]
            except Exception as e:
                print(f"Failed to initialize ResNet50: {e}")
                self.torch_available = False

    def is_blurry(self, image_path):
        """
        Phase 2 Feature: OpenCV Laplacian variance.
        Returns True if image variance drops below threshold.
        """
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                return False # Assume not blurry if read fails (better to let it pass and fail ResNet)
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            variance = cv2.Laplacian(gray, cv2.CV_64F).var()
            return (variance < self.blur_threshold), variance
        except Exception as e:
            return False, 0.0

    def get_tags(self, image_path, top_k=3):
        """
        Phase 3 Feature: Deep Learning tag classification.
        Runs the image through a forward pass of ResNet50.
        """
        if not self.torch_available or not self.model:
            return ["tagging_disabled"]
            
        try:
            input_image = Image.open(str(image_path)).convert('RGB')
            input_tensor = self.preprocess(input_image)
            input_batch = input_tensor.unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                output = self.model(input_batch)
                
            probabilities = torch.nn.functional.softmax(output[0], dim=0)
            top_prob, top_catid = torch.topk(probabilities, top_k)
            
            tags = []
            for i in range(top_prob.size(0)):
                cat = self.categories[top_catid[i]]
                tags.append(cat)
                
            return tags
        except Exception as e:
            return ["error"]
