<template>
	<div class="header">
		<h3
			class="title"
			:contenteditable="contenteditable"
			@keydown="handleKeyDown"
			@click="handleCLick"
			@blur="editNameOnBlur"
		>
			{{ print_format_name }}
		</h3>
		<button class="btn btn-sm btn-default exit-btn" @click="goToLastPage">
			<span>Exit</span>
		</button>
	</div>
</template>
<script setup>
import { ref } from "vue";
import { useMainStore } from "../../store/MainStore";
import { selectElementContents } from "../../utils";

const MainStore = useMainStore();

const contenteditable = ref(false);

const handleCLick = (e) => {
	if (!contenteditable.value) {
		contenteditable.value = true;
	}
	setTimeout(function () {
		if (document.activeElement !== e.target) {
			e.target.focus();
			selectElementContents(e.target);
		} else {
			e.target.focus();
		}
	}, 0);
};

const editNameOnBlur = (e) => {
	contenteditable.value = false;
	const new_name = e.target.innerText.trim();
	const doctype = "Print Format";
	const docname = MainStore.printDesignName;
	if (new_name === "" || new_name === docname) {
		e.target.innerText = docname;
		return;
	}
	if (new_name === docname) return;

	const callback = (r, rt) => {
		if (!r.exc) {
			$(document).trigger("rename", [doctype, docname, r.message || new_name]);
			if (locals[doctype] && locals[doctype][docname]) delete locals[doctype][docname];
			frappe.set_route();
			frappe.set_route("print-designer", new_name);
		}
	};

	frappe.call({
		method: "frappe.rename_doc",
		freeze: true,
		freeze_message: "Renaming Format Name...",
		args: {
			doctype: doctype,
			old: docname,
			new: new_name,
			merge: false,
		},
		callback: callback,
	});
};

const handleKeyDown = (e) => {
	if (["Escape", "Enter", "Tab"].indexOf(e.key) != -1) {
		e.target.blur();
	}
	if (e.key == "Tab") {
		e.preventDefault();
	}
};

const props = defineProps({
	print_format_name: String,
});
const goToLastPage = () => {
	let prev_route = frappe.get_prev_route();
	if (prev_route[0] !== "print-designer") {
		frappe.set_route(prev_route);
	} else {
		frappe.set_route();
	}
};
</script>
<style scoped lang="scss">
.header {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	padding: 0 16px;
	display: flex;
	justify-content: center;
	align-items: center;
	gap: 16px;
	height: calc(var(--navbar-height) - 1px);
	z-index: 1020;
	user-select: none;

	.title {
		flex: auto;
		font-size: var(--text-lg);
		font-weight: var(--weight-semibold);
		letter-spacing: 0.015em;
		margin-bottom: 0;
		user-select: none;
		cursor: text;
	}

	.exit-btn {
		display: flex;
		align-items: center;
		gap: 4px;
		padding: 2px 8px;
	}

	[contenteditable] {
		outline: none;
		padding: 6px 8px;
		&:hover {
			padding-bottom: 5px;
			border-bottom: 1px solid #d5c291;
		}
		&:focus {
			border-bottom: 1px solid var(--primary);
			padding-bottom: 5px;
		}
	}
}
</style>
