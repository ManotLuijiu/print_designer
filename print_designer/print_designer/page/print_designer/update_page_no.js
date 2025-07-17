// this script is injected in the page to update the page number for pdf.
const replaceText = (parentEL, className, text) => {
	const elements = parentEL.getElementsByClassName(className);
	for (let j = 0; j < elements.length; j++) {
		elements[j].textContent = text;
	}
};

const update_page_no = (clone, i, no_of_pages, print_designer) => {
	const dateObj = new Date();
	if (print_designer) {
		replaceText(clone, "page_info_page", i);
		replaceText(clone, "page_info_topage", no_of_pages);
		replaceText(clone, "page_info_date", dateObj.toLocaleDateString());
		replaceText(clone, "page_info_isodate", dateObj.toISOString());
		replaceText(clone, "page_info_time", dateObj.toLocaleTimeString());
	} else {
		replaceText(clone, "page", i);
		replaceText(clone, "topage", no_of_pages);
		replaceText(clone, "date", dateObj.toLocaleDateString());
		replaceText(clone, "isodate", dateObj.toISOString());
		replaceText(clone, "time", dateObj.toLocaleTimeString());
	}
};

const toggle_visibility = (clone, id, visibility) => {
	const element = clone.querySelector(id);
	if (element) {
		element.style.display = visibility;
	}
};

const add_wrapper = (clone, wrapper) => {
	wrapper = wrapper.cloneNode(true);
	wrapper.appendChild(clone);
	return wrapper;
};
// Helper function to compare if two elements have the same content
const areElementsEqual = (elem1, elem2) => {
	if (!elem1 || !elem2) return false;
	return elem1.innerHTML === elem2.innerHTML;
};

// Only generate different header/footers if content is actually different
const extract_elements = (template, type) => {
	const firstPageElement = template.querySelector(`#firstPage${type}`);
	const evenPageElement = template.querySelector(`#evenPage${type}`);
	const oddPageElement = template.querySelector(`#oddPage${type}`);
	const lastPageElement = template.querySelector(`#lastPage${type}`);

	// Check if we're in a copy generation context (multiple __print_designer divs)
	const printDesignerDivs = document.querySelectorAll('#__print_designer');
	const isMultipleCopies = printDesignerDivs.length > 1;
	
	// Check if template has already optimized content (marked with data-content-shared)
	const isContentShared = firstPageElement?.getAttribute('data-content-shared') === 'true';
	
	// Skip optimization if multiple copies are being generated
	if (isMultipleCopies) {
		// For copies, always use original logic to avoid conflicts
		const extracted = {
			even: evenPageElement?.cloneNode(true),
			odd: oddPageElement?.cloneNode(true),
			last: lastPageElement?.cloneNode(true),
		};

		if (extracted.even) {
			extracted.even.style.display = "block";
			evenPageElement?.remove();
		}
		if (extracted.odd) {
			extracted.odd.style.display = "block";
			oddPageElement?.remove();
		}
		if (extracted.last) {
			extracted.last.style.display = "block";
			lastPageElement?.remove();
		}

		firstPageElement.style.display = "none";
		if (extracted.even) extracted.even = add_wrapper(extracted.even, template);
		if (extracted.odd) extracted.odd = add_wrapper(extracted.odd, template);
		if (extracted.last) extracted.last = add_wrapper(extracted.last, template);
		firstPageElement.style.display = "block";

		return extracted;
	}
	
	if (isContentShared) {
		// Template has already optimized content, clean up empty elements
		if (evenPageElement?.innerHTML.trim() === '') evenPageElement.remove();
		if (oddPageElement?.innerHTML.trim() === '') oddPageElement.remove();
		if (lastPageElement?.innerHTML.trim() === '') lastPageElement.remove();
		
		// Return the same element for all page types
		const sharedElement = firstPageElement.cloneNode(true);
		sharedElement.style.display = "block";
		sharedElement.removeAttribute('data-content-shared');
		
		return {
			even: add_wrapper(sharedElement.cloneNode(true), template),
			odd: add_wrapper(sharedElement.cloneNode(true), template),
			last: add_wrapper(sharedElement.cloneNode(true), template),
		};
	}

	// Check if all elements have the same content as firstPage
	const evenSameAsFirst = areElementsEqual(firstPageElement, evenPageElement);
	const oddSameAsFirst = areElementsEqual(firstPageElement, oddPageElement);
	const lastSameAsFirst = areElementsEqual(firstPageElement, lastPageElement);

	// If all content is the same, just reuse the first page element
	if (evenSameAsFirst && oddSameAsFirst && lastSameAsFirst) {
		// Remove duplicate elements since they're identical
		evenPageElement?.remove();
		oddPageElement?.remove();
		lastPageElement?.remove();
		
		// Return the same element for all page types
		const sharedElement = firstPageElement.cloneNode(true);
		sharedElement.style.display = "block";
		
		return {
			even: add_wrapper(sharedElement.cloneNode(true), template),
			odd: add_wrapper(sharedElement.cloneNode(true), template),
			last: add_wrapper(sharedElement.cloneNode(true), template),
		};
	}

	// Original logic for when content is actually different
	const extracted = {
		even: evenPageElement?.cloneNode(true),
		odd: oddPageElement?.cloneNode(true),
		last: lastPageElement?.cloneNode(true),
	};

	// Set display and clean up only if elements exist and are different
	if (extracted.even && !evenSameAsFirst) {
		extracted.even.style.display = "block";
		evenPageElement.remove();
	} else if (evenSameAsFirst) {
		extracted.even = firstPageElement.cloneNode(true);
		extracted.even.style.display = "block";
		evenPageElement?.remove();
	}

	if (extracted.odd && !oddSameAsFirst) {
		extracted.odd.style.display = "block";
		oddPageElement.remove();
	} else if (oddSameAsFirst) {
		extracted.odd = firstPageElement.cloneNode(true);
		extracted.odd.style.display = "block";
		oddPageElement?.remove();
	}

	if (extracted.last && !lastSameAsFirst) {
		extracted.last.style.display = "block";
		lastPageElement.remove();
	} else if (lastSameAsFirst) {
		extracted.last = firstPageElement.cloneNode(true);
		extracted.last.style.display = "block";
		lastPageElement?.remove();
	}

	// Wrap elements with template structure
	firstPageElement.style.display = "none";
	if (extracted.even) extracted.even = add_wrapper(extracted.even, template);
	if (extracted.odd) extracted.odd = add_wrapper(extracted.odd, template);
	if (extracted.last) extracted.last = add_wrapper(extracted.last, template);
	firstPageElement.style.display = "block";

	return extracted;
};

const clone_and_update = (
	selector,
	no_of_pages,
	print_designer,
	type = null,
	is_dynamic = true
) => {
	const template = document.querySelector(selector);
	let elements;
	if (print_designer) {
		elements = extract_elements(template, type);
	}
	const fragment = document.createDocumentFragment();
	for (let i = 2; i <= (is_dynamic ? no_of_pages : 4); i++) {
		let clone;
		if (print_designer) {
			// print designer have different header and footer for even, odd and last page (4)
			if (i == (is_dynamic ? no_of_pages : 4)) {
				clone = elements.last?.cloneNode(true);
			} else if (i % 2 == 0) {
				clone = elements.even?.cloneNode(true);
			} else {
				clone = elements.odd?.cloneNode(true);
			}
		} else {
			clone = template.cloneNode(true);
		}
		if (is_dynamic) {
			update_page_no(clone, i, no_of_pages, print_designer);
		}
		fragment.appendChild(clone);
	}
	template.parentElement.appendChild(fragment);
	if (is_dynamic) {
		update_page_no(template, 1, no_of_pages, print_designer);
	}
};
