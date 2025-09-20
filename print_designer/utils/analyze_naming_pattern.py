import frappe

def analyze_wht_certificate_naming():
	"""Analyze current WHT Certificate naming pattern"""
	# Get sample WHT Certificate names to understand the pattern
	wht_certs = frappe.db.get_all('Withholding Tax Certificate',
		fields=['name', 'creation'],
		order_by='creation desc',
		limit=10
	)

	print('📋 Current WHT Certificate naming pattern:')
	print('=' * 50)
	for cert in wht_certs:
		print(f'  {cert.name} (created: {cert.creation})')

	# Analyze the pattern
	if wht_certs:
		sample_name = wht_certs[0].name
		parts = sample_name.split('-')
		print(f'\n🔍 Pattern Analysis from: {sample_name}')
		print(f'  - Prefix: {parts[0]}')
		print(f'  - Year-Month: {parts[1]}')
		print(f'  - Sequential: {parts[2]}')
		print(f'  - Format: PREFIX-YYMM-NNNNN')

		# Extract YYMM for current period
		current_yymm = parts[1]
		print(f'\n🎯 Target PND3 Format:')
		print(f'  - Current WHT: WHTC-{current_yymm}-NNNNN')
		print(f'  - New PND3: PND3-{current_yymm}-NNNNN')
		print(f'  - Examples:')
		print(f'    • PND3-{current_yymm}-00001 (first of month)')
		print(f'    • PND3-{current_yymm}-00002 (second of month)')

		# Show next month examples
		yy = int(current_yymm[:2])
		mm = int(current_yymm[2:])

		# Calculate next few months
		next_months = []
		for i in range(1, 4):
			new_mm = mm + i
			new_yy = yy
			if new_mm > 12:
				new_mm = new_mm - 12
				new_yy = yy + 1
			next_months.append(f"{new_yy:02d}{new_mm:02d}")

		print(f'  - Next months reset examples:')
		for next_yymm in next_months:
			print(f'    • PND3-{next_yymm}-00001 (first of new month)')

		return current_yymm
	else:
		print('❌ No WHT Certificates found to analyze pattern')
		return None