from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from typing import Tuple, Optional
import logging
import threading
import time
from queue import Queue

class TimeoutException(Exception):
    pass

class TranslationModel:
    def __init__(self, model_name: str = "LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.logger = logging.getLogger(__name__)
        
    def load_model(self, device: Optional[str] = None) -> None:
        """Load the model and tokenizer with specified configurations."""
        try:
            self.logger.info(f"Loading model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                revision="main",
                torch_dtype=torch.bfloat16,
                device_map="auto" if device is None else device,
                low_cpu_mem_usage=True,
            )
            self.logger.info("Model loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            raise

    def generate_with_timeout(self, input_ids, timeout_seconds=30, **kwargs):
        """Run model generation with timeout using a separate thread."""
        result_queue = Queue()
        error_queue = Queue()

        def generate_fn():
            try:
                with torch.no_grad():
                    result = self.model.generate(input_ids.to(self.model.device), **kwargs)
                result_queue.put(result)
            except Exception as e:
                error_queue.put(e)

        # Start generation in a separate thread
        thread = threading.Thread(target=generate_fn)
        thread.daemon = True  # Thread will be killed if main program exits
        thread.start()
        
        # Wait for the thread to complete or timeout
        thread.join(timeout_seconds)
        
        if thread.is_alive():
            # If thread is still running after timeout
            self.logger.error("Generation timed out")
            raise TimeoutException("Translation took too long. Please try again with shorter text.")
        
        # Check for errors
        if not error_queue.empty():
            raise error_queue.get()
        
        # Get the result
        if not result_queue.empty():
            return result_queue.get()
        else:
            raise TimeoutException("No result produced within timeout period")

    def translate(self, text: str, max_length: int = 256) -> str:
        """Perform translation using the loaded model."""
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model and tokenizer must be loaded before translation")
        
        try:
            self.logger.info("Preparing chat template")
            
            # Determine translation direction and create appropriate system message
            if "Translate this Korean text to English:" in text:
                system_content = "You are EXAONE model from LG AI Research. Translate the following text to English."
                text = text.replace("Translate this Korean text to English:", "").strip()
            elif "Translate this English text to Korean:" in text:
                system_content = "You are EXAONE model from LG AI Research. Translate the following text to Korean."
                text = text.replace("Translate this English text to Korean:", "").strip()
            else:
                system_content = "You are EXAONE model from LG AI Research. Translate the following text appropriately."

            # Create messages for chat template
            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": text}
            ]
            
            self.logger.info("Applying chat template...")
            input_ids = self.tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt"
            )
            self.logger.info("Chat template applied")
            
            self.logger.info("Starting model generation")
            generation_args = {
                "max_new_tokens": 128,
                "do_sample": False,
                "eos_token_id": self.tokenizer.eos_token_id,
            }
            
            # Try generation with timeout
            try:
                outputs = self.generate_with_timeout(input_ids, timeout_seconds=20, **generation_args)
                self.logger.info("Model generation completed")
            except TimeoutException:
                # If first attempt times out, try with shorter max_tokens
                self.logger.warning("First attempt timed out, trying with reduced tokens")
                generation_args["max_new_tokens"] = 64
                outputs = self.generate_with_timeout(input_ids, timeout_seconds=10, **generation_args)
            
            self.logger.info("Starting decoding")
            translation = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Clean up translation by removing the input text and assistant prefix
            try:
                # Remove the input text first
                translation = translation.split(text)[-1].strip()
                # Remove the assistant prefix if present
                if "[|assistant|]" in translation:
                    translation = translation.split("[|assistant|]")[-1].strip()
            except:
                pass
            
            self.logger.info("Decoding completed")
            self.logger.info(f"Raw translation: {translation}")
            
            return translation
        except TimeoutException as te:
            self.logger.error("Translation timed out")
            raise te
        except Exception as e:
            self.logger.error(f"Translation error: {str(e)}")
            raise

    def __del__(self):
        """Cleanup method to free GPU memory."""
        try:
            if self.model is not None:
                del self.model
            if self.tokenizer is not None:
                del self.tokenizer
            torch.cuda.empty_cache()
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Error during cleanup: {str(e)}")

# Example usage
if __name__ == "__main__":
    translator = TranslationModel()
    translator.load_model()
    print("Model loaded successfully")
