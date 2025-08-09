import re
import os
import subprocess
import tempfile

def insert_images_in_latex(input_file, image_paths):
    output_file = os.path.split(input_file)[0]+"/output.tex"
    try:
        # Read the input file
        with open(input_file, 'r') as file:
            content = file.read()

        # Define the regex pattern to match <img> tags
        pattern = r'<img\s*>(.*?)</img>'

        # Initialize the image path iterator
        image_iter = iter(image_paths)

        # Function to replace matched patterns
        def replace_img(match):
            if not image_path:
                return ''
            try:
                image_path = next(image_iter)
            except StopIteration:
                print("Warning: More <img> tags than provided image paths. Reusing the last image path.")
                image_path = image_paths[-1] if image_paths else None

            caption = match.group(1).strip()

            # Construct the LaTeX command
            latex_cmd = f"\\begin{{figure}}[htbp]\n\\centering\n"
            latex_cmd += f"\\includegraphics[width=0.8\\textwidth]{{{image_path}}}\n"
            
            if caption:
                latex_cmd += f"\\caption{{{caption}}}\n"
            
            latex_cmd += f"\\label{{fig:{image_path.split('/')[-1].split('.')[0]}}}\n"
            latex_cmd += "\\end{figure}"

            return latex_cmd

        # Replace all occurrences of <img> tags
        new_content = re.sub(pattern, replace_img, content, flags=re.DOTALL)

        # Check if there are unused image paths
        unused_images = list(image_iter)
        if unused_images:
            print(f"Warning: {len(unused_images)} image path(s) were not used: {', '.join(unused_images)}")

        # Prepare the complete LaTeX document
        full_document = f"""\\documentclass{{article}}
\\usepackage{{graphicx}}
\\usepackage{{float}}

\\begin{{document}}

{new_content}

\\end{{document}}
"""

        # Write the complete LaTeX document to the output file
        with open(output_file, 'a') as file:
            file.write(full_document)

        print(f"Successfully processed {input_file} and saved result to {output_file}")

    except FileNotFoundError:
        print(f"Error: The file {input_file} was not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    return output_file




def latex_to_pdf(latex_file_path,output_path):
    """
    Convert a LaTeX file to PDF using pdflatex.

    Args:
    latex_file_path (str): Path to the input LaTeX file

    Returns:
    str: Path to the output PDF file, or None if conversion failed
    """
    try:
        # Get the directory and filename of the input file
        input_dir, input_filename = os.path.split(latex_file_path)
        input_basename = os.path.splitext(input_filename)[0]

        # Change to the input file's directory
        original_dir = os.getcwd()
        if not input_dir:
            input_dir = './'
        os.chdir(input_dir)

        # Run pdflatex and capture output
        result = subprocess.run(['pdflatex', '-interaction=nonstopmode', input_filename], 
                                check=True, capture_output=True, text=True)

        # Print pdflatex output for debugging
        print("pdflatex output:")
        print(result.stdout)
        print("pdflatex error output:")
        print(result.stderr)

        # Get the path of the created PDF
        # pdf_path = os.path.join(input_dir, f"{input_basename}.pdf")
        pdf_path = output_path
        # pdf_path= output_path

        # Check if PDF was created
        if os.path.exists(pdf_path):
            print(f"PDF created successfully: {pdf_path}")
            return pdf_path
        else:
            print("PDF creation failed.")
            return None

    except subprocess.CalledProcessError as e:
        print(f"Error: PDF conversion failed for {latex_file_path}")
        print("pdflatex error output:")
        print(e.output)
        return None

    finally:
        # Change back to the original directory
        os.chdir(original_dir)
    

def convert_latex_to_pdf(latex_code, output_filename="output.pdf", cleanup=True):
    """
    Convert LaTeX code to a PDF file.
    
    Parameters:
    -----------
    latex_code : str
        The LaTeX code to convert.
    output_filename : str, optional
        Name of the output PDF file (default: "output.pdf").
    cleanup : bool, optional
        Whether to remove temporary files after conversion (default: True).
        
    Returns:
    --------
    bool
        True if the conversion was successful, False otherwise.
    """
    try:
        # Create a temporary directory for our LaTeX files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary .tex file
            tex_file = os.path.join(temp_dir, "temp.tex")
            
            # Write the LaTeX code to the file
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(latex_code)
            
            # Run pdflatex to convert the .tex file to PDF
            process = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", temp_dir, tex_file],
                capture_output=True,
                text=True
            )
            
            if process.returncode != 0:
                print(f"LaTeX compilation error: {process.stderr}")
                return False
            
            # Copy the generated PDF to the output filename
            temp_pdf = os.path.join(temp_dir, "temp.pdf")
            if os.path.exists(temp_pdf):
                # Copy the PDF to the desired output location
                with open(temp_pdf, "rb") as src, open(output_filename, "wb") as dst:
                    dst.write(src.read())
                
                print(f"PDF successfully created: {output_filename}")
                return True
            else:
                print("PDF generation failed. Check your LaTeX code.")
                return False
    
    except Exception as e:
        print(f"Error in LaTeX to PDF conversion: {str(e)}")
        return False

# Example usage
# if __name__ == "__main__":
#     latex_code = r"""
#     \documentclass{article}
#     \begin{document}
#     Hello, world! This is a simple \LaTeX\ document.
#     \end{document}
#     """
    
#     latex_to_pdf(latex_code, "hello_world.pdf")




# Example usage
# pdf_path = latex_to_pdf('output.tex', 'notes.pdf')


# Example usage
# insert_images_in_latex('input.tex', 'output.tex', ['image1.png', 'image2.png', 'image3.png'])