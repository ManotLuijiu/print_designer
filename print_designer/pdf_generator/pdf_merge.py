from io import BytesIO

from pypdf import PdfWriter, Transformation, PdfReader, PageObject


class PDFTransformer:
	def __init__(self, browser):
		self.browser = browser
		self.body_pdf = browser.body_pdf
		self.is_print_designer = browser.is_print_designer
		self._set_header_pdf()
		self._set_footer_pdf()
		if not self.header_pdf and not self.footer_pdf:
			return
		self.no_of_pages = len(self.body_pdf.pages)
		self.encrypt_password = self.browser.options.get("password", None)
		# if not header / footer then return body pdf

	def _set_header_pdf(self):
		self.header_pdf = None
		if hasattr(self.browser, "header_pdf"):
			self.header_pdf = self.browser.header_pdf
			self.is_header_dynamic = self.browser.is_header_dynamic

	def _set_footer_pdf(self):
		self.footer_pdf = None
		if hasattr(self.browser, "footer_pdf"):
			self.footer_pdf = self.browser.footer_pdf
			self.is_footer_dynamic = self.browser.is_footer_dynamic

	def transform_pdf(self, output=None):
		import frappe
		header = self.header_pdf
		body = self.body_pdf
		footer = self.footer_pdf

		# Debug logging
		copy_count = getattr(self.browser, 'copy_count', 0)
		frappe.logger().info(f"PDFTransformer Debug - copy_count: {copy_count}, has_header: {bool(header)}, has_footer: {bool(footer)}")
		frappe.logger().info(f"Browser options: {getattr(self.browser, 'options', {})}")

		if not header and not footer:
			# Check if we need to generate copies
			if hasattr(self.browser, 'copy_count') and self.browser.copy_count > 1:
				frappe.logger().info(f"Generating {self.browser.copy_count} copies (no header/footer)")
				return self._generate_copies(body)
			return body

		body_height = body.pages[0].mediabox.top
		body_transform = header_height = footer_height = header_body_top = 0

		if footer:
			footer_height = footer.pages[0].mediabox.top
			body_transform = footer_height

		if header:
			header_height = header.pages[0].mediabox.top
			header_transform = body_height + footer_height
			header_body_top = header_height + body_height + footer_height

		if header and not self.is_header_dynamic:
			for h in header.pages:
				self._transform(h, header_body_top, header_transform)

		for p in body.pages:
			if header_body_top:
				self._transform(p, header_body_top, body_transform)
			if header:
				if self.is_header_dynamic:
					p.merge_page(self._transform(header.pages[p.page_number], header_body_top, header_transform))
				elif self.is_print_designer:
					if p.page_number == 0:
						p.merge_page(header.pages[0])
					elif p.page_number == self.no_of_pages - 1:
						p.merge_page(header.pages[3])
					elif p.page_number % 2 == 0:
						p.merge_page(header.pages[2])
					else:
						p.merge_page(header.pages[1])
				else:
					p.merge_page(header.pages[0])

			if footer:
				if self.is_footer_dynamic:
					p.merge_page(footer.pages[p.page_number])
				elif self.is_print_designer:
					if p.page_number == 0:
						p.merge_page(footer.pages[0])
					elif p.page_number == self.no_of_pages - 1:
						p.merge_page(footer.pages[3])
					elif p.page_number % 2 == 0:
						p.merge_page(footer.pages[2])
					else:
						p.merge_page(footer.pages[1])
				else:
					p.merge_page(footer.pages[0])

		if output:
			output.append_pages_from_reader(body)
			return output

		writer = PdfWriter()
		writer.append_pages_from_reader(body)
		if self.encrypt_password:
			writer.encrypt(self.encrypt_password)

		# Check if we need to apply watermarks or generate copies
		watermark_mode = getattr(self.browser, 'watermark_mode', None)
		copy_watermark = getattr(self.browser, 'copy_watermark', False)
		
		if watermark_mode and copy_watermark:
			frappe.logger().info(f"Applying watermarks with mode: {watermark_mode}")
			merged_pdf_data = self.get_file_data_from_writer(writer)
			return self._generate_watermarked_pdf(merged_pdf_data)
		elif hasattr(self.browser, 'copy_count') and self.browser.copy_count > 1:
			frappe.logger().info(f"Generating {self.browser.copy_count} copies (with header/footer)")
			merged_pdf_data = self.get_file_data_from_writer(writer)
			return self._generate_copies_from_data(merged_pdf_data)
		return self.get_file_data_from_writer(writer)

	def _transform(self, page, page_top, ty):
		transform = Transformation().translate(ty=ty)
		page.mediabox.upper_right = (page.mediabox.right, page_top)
		page.add_transformation(transform)
		return page

	def get_file_data_from_writer(self, writer_obj):
		# https://docs.python.org/3/library/io.html
		stream = BytesIO()
		writer_obj.write(stream)

		# Change the stream position to start of the stream
		stream.seek(0)

		# Read up to size bytes from the object and return them
		return stream.read()

	def _generate_copies(self, body_pdf):
		"""Generate multiple copies of PDF with watermarks directly from PdfReader"""
		import frappe
		copy_count = getattr(self.browser, 'copy_count', 2)
		print(f"Generating {copy_count} copies of the PDF")
		copy_labels = getattr(self.browser, 'copy_labels', [frappe._("Original"), frappe._("Copy")])
		copy_watermark = getattr(self.browser, 'copy_watermark', True)

		final_writer = PdfWriter()

		# Generate each copy
		for i in range(copy_count):
			label = copy_labels[i] if i < len(copy_labels) else f"COPY {i}"
			
			# Add all pages from body_pdf to final_writer
			for page in body_pdf.pages:
				if copy_watermark:
					# Add watermark to the page
					watermarked_page = self._add_watermark_to_page(page, label)
					final_writer.add_page(watermarked_page)
				else:
					final_writer.add_page(page)

		if self.encrypt_password:
			final_writer.encrypt(self.encrypt_password)

		return self.get_file_data_from_writer(final_writer)

	def _generate_copies_from_data(self, pdf_data):
		"""Generate multiple copies from PDF data"""
		import frappe
		copy_count = getattr(self.browser, 'copy_count', 2)
		copy_labels = getattr(self.browser, 'copy_labels', [frappe._("Original"), frappe._("Copy")])
		copy_watermark = getattr(self.browser, 'copy_watermark', True)

		# Read the PDF data
		pdf_stream = BytesIO(pdf_data)
		pdf_reader = PdfReader(pdf_stream)
		
		final_writer = PdfWriter()

		# Generate each copy
		for i in range(copy_count):
			label = copy_labels[i] if i < len(copy_labels) else f"COPY {i}"
			
			# Add all pages from original PDF to final_writer
			for page in pdf_reader.pages:
				if copy_watermark:
					# Add watermark to the page
					watermarked_page = self._add_watermark_to_page(page, label)
					final_writer.add_page(watermarked_page)
				else:
					final_writer.add_page(page)

		if self.encrypt_password:
			final_writer.encrypt(self.encrypt_password)

		return self.get_file_data_from_writer(final_writer)

	def _generate_watermarked_pdf(self, merged_pdf_data):
		"""Generate PDF with watermarks based on watermark mode"""
		import frappe
		from io import BytesIO
		
		pdf_reader = PdfReader(BytesIO(merged_pdf_data))
		final_writer = PdfWriter()
		
		watermark_mode = getattr(self.browser, 'watermark_mode', 'sequence')
		watermark_labels = getattr(self.browser, 'watermark_labels', [frappe._("Original"), frappe._("Copy")])
		
		# Add pages with appropriate watermarks based on mode
		for page_num, page in enumerate(pdf_reader.pages):
			label = None
			
			if watermark_mode == "first_page_only":
				# Only first page gets watermark
				if page_num == 0:
					label = watermark_labels[0] if watermark_labels else frappe._("Original")
			elif watermark_mode == "all_pages":
				# All pages get the same watermark
				label = watermark_labels[0] if watermark_labels else frappe._("Copy")
			elif watermark_mode == "sequence":
				# Pages alternate between labels
				label_index = page_num % len(watermark_labels) if watermark_labels else page_num % 2
				if watermark_labels:
					label = watermark_labels[label_index]
				else:
					label = frappe._("Original") if label_index == 0 else frappe._("Copy")
			
			if label:
				watermarked_page = self._add_watermark_to_page(page, label)
				final_writer.add_page(watermarked_page)
			else:
				final_writer.add_page(page)
		
		if self.encrypt_password:
			final_writer.encrypt(self.encrypt_password)
		
		return self.get_file_data_from_writer(final_writer)

	def _add_watermark_to_page(self, page, label):
		"""Add text label to page by creating a text overlay"""
		import frappe
		from io import BytesIO
		try:
			# Try to create a simple text overlay using reportlab (if available)
			from reportlab.pdfgen import canvas
			from reportlab.lib.pagesizes import letter
			
			# Get page dimensions  
			width = float(page.mediabox.width)
			height = float(page.mediabox.height)
			
			# Create a text overlay PDF
			packet = BytesIO()
			can = canvas.Canvas(packet, pagesize=(width, height))
			
			# Set text properties
			can.setFont("Helvetica-Bold", 12)
			can.setFillColorRGB(0.7, 0.7, 0.7)  # Light gray
			
			# Position text in top-right corner
			can.drawString(width - 100, height - 30, label)
			can.save()
			
			# Move to the beginning of the StringIO buffer
			packet.seek(0)
			
			# Create a new PDF reader for the overlay
			from pypdf import PdfReader
			overlay_pdf = PdfReader(packet)
			
			# Merge the overlay with the original page
			page.merge_page(overlay_pdf.pages[0])
			
			return page
			
		except ImportError:
			# Fallback: Add a simple annotation-style text
			try:
				from pypdf.generic import DictionaryObject, TextStringObject, ArrayObject, FloatObject, NameObject, BooleanObject
				
				# Create a simple text annotation (this might not be visible in all viewers)
				width = float(page.mediabox.width)
				height = float(page.mediabox.height)
				
				annotation = DictionaryObject({
					NameObject("/Type"): NameObject("/Annot"),
					NameObject("/Subtype"): NameObject("/Text"),
					NameObject("/Rect"): ArrayObject([FloatObject(width-100), FloatObject(height-30), 
										FloatObject(width-10), FloatObject(height-10)]),
					NameObject("/Contents"): TextStringObject(label),
					NameObject("/Open"): BooleanObject(True)
				})
				
				if "/Annots" in page:
					page["/Annots"].append(annotation)
				else:
					page[NameObject("/Annots")] = ArrayObject([annotation])
					
				return page
			except Exception as e:
				frappe.logger().info(f"Could not add text annotation: {e}")
				return page
		except Exception as e:
			frappe.logger().info(f"Could not add text overlay: {e}")
			return page
