# Korean-English Translator

A modern desktop application for bidirectional Korean-English translation with word-level translation capabilities.

## Features

- **Bidirectional Translation**
  - Korean to English
  - English to Korean
  - Real-time translation with modern UI

- **Advanced Translation Features**
  - Word-level translation with context
  - Direct and contextual meanings for selected words
  - Hover tooltips for translations

- **Modern User Interface**
  - Clean, dual-editor layout
  - Intuitive translation buttons
  - Loading indicators with progress visualization
  - Easy text selection and word lookup

## Technical Details

### Model
- Uses LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct model
- Supports both CPU and GPU inference
- Optimized with bfloat16 precision
- Implements timeout protection and fallback strategies

### Requirements

```bash
Python 3.8+
PyQt6
transformers
torch
```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Translator.git
cd Translator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Usage

1. Run the application:
```bash
python main.py
```

2. Basic Translation:
   - Enter text in either the Korean or English editor
   - Click the corresponding translation button
   - View the translation in the opposite editor

3. Word Translation:
   - After translation, select any word in either editor
   - A tooltip will appear showing:
     - Direct translation of the word
     - Contextual meaning (if available)

## Project Structure

```
Translator/
├── main.py              # Main application entry point
├── model_setup.py       # Translation model configuration
├── translator_ui.py     # PyQt6 UI implementation
├── korean_processor.py  # Korean text processing
├── cache_manager.py     # Translation caching system
└── requirements.txt     # Project dependencies
```

## Performance Notes

- First-time startup may take longer due to model downloading and installing.
- Translation speed depends on:
  - Text length
  - Available computing resources
  - Selected translation parameters
  
CUDA RECOMMENDED FOR OPTIMAL PERFORMANCE

## Known Limitations

- Long text translations may timeout on slower systems
- Word translations are context-dependent and may vary

## Contributing

Feel free to submit issues and enhancement requests! 