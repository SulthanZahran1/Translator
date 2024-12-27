import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_translation():
    try:
        # Load model and tokenizer
        logger.info("Loading model and tokenizer...")
        model_name = "LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct"
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            revision="main",
            torch_dtype=torch.bfloat16,
            device_map="auto",
            low_cpu_mem_usage=True,
        )
        logger.info("Model loaded successfully")

        # Test texts
        test_texts = [
            "Hello, how are you?",
            "I love programming",
            "The weather is nice today"
        ]

        logger.info("\nStarting translation tests...")
        
        for text in test_texts:
            logger.info(f"\nTesting with text: {text}")
            
            # Prepare input using chat template
            messages = [
                {"role": "system", 
                 "content": "You are EXAONE model from LG AI Research. Translate the following text to Korean."},
                {"role": "user", "content": text}
            ]
            
            logger.info("Applying chat template...")
            input_ids = tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt"
            )
            logger.info("Chat template applied")
            
            # Generate
            logger.info("Generating translation...")
            with torch.no_grad():
                outputs = model.generate(
                    input_ids.to(model.device),
                    max_new_tokens=128,
                    do_sample=False,
                    eos_token_id=tokenizer.eos_token_id,
                )
            
            # Decode
            translation = tokenizer.decode(outputs[0], skip_special_tokens=True)
            logger.info(f"Raw output: {translation}")
            
            # Clean up translation (remove the input text from output)
            try:
                translation = translation.split(text)[-1].strip()
            except:
                pass
            
            logger.info(f"Cleaned translation: {translation}")
            logger.info("-" * 50)

    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
        raise

if __name__ == "__main__":
    test_translation() 