import os

def generate_xmp(image_path, tags):
    """
    Phase 4 Feature: Generates an Adobe Lightroom compatible .xmp sidecar file
    for a given image file, injecting AI tags as keywords.
    """
    file_name, _ = os.path.splitext(image_path)
    xmp_file = file_name + ".xmp"
    
    # Constructing the XMP XML structure
    bag_items = "\n".join([f"     <rdf:li>{tag}</rdf:li>" for tag in tags])
    
    xmp_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:dc="http://purl.org/dc/elements/1.1/">
   <dc:subject>
    <rdf:Bag>
{bag_items}
    </rdf:Bag>
   </dc:subject>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>"""

    try:
        with open(xmp_file, "w", encoding="utf-8") as f:
            f.write(xmp_content)
        return True
    except Exception as e:
        print(f"Failed to write XMP: {e}")
        return False
