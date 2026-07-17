<template>
	<div
		class="properties-container"
		@keydown.stop
		@keyup.stop
		:ref="
			(el) => {
				MainStore.propertiesContainer = el;
			}
		"
	>
		<Icons style="display: none" />
		<div class="primary-actions">
			<button
				class="btn btn-sm add-data-button"
				@click="(event) => (MainStore.openJinjaModal = true)"
			>
				Custom Data
			</button>
			<button
				class="btn btn-sm btn-primary"
				@click="
					(event) => {
						if (MainStore.mode == 'pdfSetup') {
							MainStore.mode = 'editing';
						}
						ElementStore.saveElements();
						event.target.blur();
					}
				"
			>
				Save
			</button>
		</div>
		<AppPropertiesPanelSection
			v-for="section in MainStore.propertiesPanel"
			:section="section"
			:key="section.title ? section.title.replace(' ', '') : section.name"
		/>
	</div>
</template>
<script setup>
import { useMainStore } from "../../store/MainStore";
import { useElementStore } from "../../store/ElementStore";
import { createPropertiesPanel } from "../../PropertiesPanelState";
import AppPropertiesPanelSection from "./AppPropertiesPanelSection.vue";
import { onMounted } from "vue";
import Icons from "../../icons/Icons.vue";

const MainStore = useMainStore();
const ElementStore = useElementStore();
onMounted(() => createPropertiesPanel());
</script>
<style deep lang="scss">
.properties-container {
	* {
		user-select: none;
	}
	cursor: default;
	position: relative;
	overflow: auto;
	.designer-icon {
		height: 24px;
		width: 24px;
		fill: var(--text-muted);
	}
	/* Properties panel icons using --icon-stroke variable */
	.flex-container svg,
	.panel-container svg {
		--icon-stroke: var(--text-muted);
	}
	.flex-container svg:hover,
	.panel-container svg:hover {
		--icon-stroke: var(--primary);
	}
	/* Ensure IconsUse icons in properties panel are visible */
	.flex-container svg use,
	.panel-container svg use {
		stroke: var(--icon-stroke);
	}
	.primary-actions {
		display: flex;
		justify-content: space-between;
		align-items: center;
		background-color: var(--subtle-fg);
		padding: 5px 10px;
		.btn {
			background-color: var(--bg-color);
			font-size: var(--text-sm) !important;
			font-size: var(--weight-regular);
		}
		.btn-primary {
			background-color: var(--btn-primary);
		}
		button {
			margin: 5px 10px;
			min-width: 60px;
			.button-with-icon {
				margin: 2px 10px 2px 0px;
				font-size: 16px;
			}
		}
	}
	.secondary-actions {
		@extend .primary-actions;
		background-color: var(--bg-color);
		.add-data-button {
			flex: 1;
			background-color: var(--subtle-fg);
		}
	}
	.text-type-container,
	.align-items-container {
		border-top: 1px solid var(--border-color);
	}
	.text-type-container {
		display: flex;
		justify-content: center;
		align-items: center;
		background-color: var(--subtle-fg);
		.text-type {
			padding: 6px 16px;
			margin: 6px 0px;
		}
		.text-type-active {
			background-color: var(--control-bg);
			box-shadow: var(--card-shadow);
			border-radius: var(--border-radius);
		}
	}
	.align-items-container {
		padding: 10px 8px;
		display: flex;
		.align-container {
			display: flex;
			width: 50%;
			justify-content: space-around;
			&:last-child {
				border-left: 1px solid var(--border-color);
			}
		}
	}
	.border-container {
		display: flex;
		align-items: center;
		.designer-icon {
			margin-left: 3.5px;
		}
	}
	.section-title {
		margin: 6px 0px 2px 8px;
		padding-bottom: 6px;
		border-bottom: 1px solid var(--border-color);
		font-weight: 500;
		font-size: 12px;
	}
	.main-label {
		flex: 2;
		margin-left: 3.5px;
		margin-top: 5px;
		margin-bottom: 4px;
		font-size: 10px;
		color: var(--text-muted);
		vertical-align: middle;
		font-weight: 400;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.panel-container {
		display: flex !important;
		justify-content: space-between;
		align-items: center;
		margin: 0px 9px;
		&.panel-border-top {
			margin-top: 8px;
			border-top: 1px solid var(--border-color);
		}
		&.panel-border-bottom {
			margin-bottom: 8px;
			border-bottom: 1px solid var(--border-color);
		}
		.flex-container {
			display: flex !important;
			margin-top: 0px;
		}
		.flex-container.flex-column {
			flex-direction: column;
			margin-top: 3.5px;
		}
	}
	.panel-input {
		font-size: 10px;
		color: var(--invert-neutral);
		background-color: var(--fg-color);
		border-bottom: 1px solid var(--border-color);
		border-radius: 0px;
		box-shadow: none;
		flex: 5;
		padding: 0.375rem 0.25rem;
		&:focus {
			box-shadow: none;
			border-bottom-color: var(--primary);
		}
		&:after {
			left: 70px;
			font-size: 11px;
		}
	}
	.settings-section {
		padding: 8px 5px;
		border-top: 1px solid var(--border-color);
	}
	.frappeControl {
		padding: 4px 15px;
		width: 100%;
		.main-label {
			margin-top: 2px;
		}
		.awesomplete {
			& > ul {
				min-width: 210px !important;
			}
		}
		.frappe-control {
			input {
				font-size: 12px;
			}
			&[data-fieldtype="Select"] {
				select {
					font-size: 11px;
				}
				.select-icon {
					top: 4px;
					right: 6px;
				}
			}
			&[data-fieldtype="Color"] {
				input {
					font-size: 11.5px;
					padding-left: 29px;
					font-weight: 300;
				}
				.input-active {
					border: 1px solid var(--primary) !important;
				}
				.selected-color {
					width: 18px;
					height: 18px;
					left: 6px;
				}
			}
		}
	}
	.form-group .form-control {
		border: 1px solid transparent !important;
		&:focus {
			box-shadow: none;
			border: 1px solid var(--primary) !important;
		}
	}
	.control-label {
		font-size: 11px;
	}
	.borderColorSelector {
		margin-top: 10px;
	}
}
.picker-arrow.arrow {
	display: none;
}

/* Border Toggle Letter Boxes - Simple styled like Help Tooltip */
.border-toggle-box {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	width: 24px;
	height: 24px;
	font-size: 11px;
	font-weight: 600;
	border-radius: 4px;
	cursor: pointer;
	transition: all 0.15s ease;
	margin: 2px;
	border: 1px solid transparent;
	/* Default inactive state - dark border, light fill */
	background-color: var(--bg-color);
	color: var(--text-muted);
	border-color: var(--text-muted);
}

.border-toggle-box:hover {
	border-color: var(--primary);
	color: var(--primary);
}

/* Active state - primary background, white text */
.border-toggle-active {
	background-color: var(--primary);
	color: white;
	border-color: var(--primary);
}

.border-toggle-active:hover {
	color: white;
}

/* Individual toggle box styles - borders on appropriate sides */
.border-toggle-all {
	border: 2px solid var(--text-muted);
}
.border-toggle-all:hover {
	border-color: var(--primary);
}
.border-toggle-all.border-toggle-active {
	border-color: white;
}

.border-toggle-left {
	border-left: 3px solid var(--text-muted);
	border-top: 1px solid var(--text-muted);
	border-right: 1px solid var(--text-muted);
	border-bottom: 1px solid var(--text-muted);
}
.border-toggle-left:hover {
	border-color: var(--primary);
}
.border-toggle-left.border-toggle-active {
	border-color: var(--primary);
	background-color: var(--primary);
}

.border-toggle-right {
	border-left: 1px solid var(--text-muted);
	border-top: 1px solid var(--text-muted);
	border-right: 3px solid var(--text-muted);
	border-bottom: 1px solid var(--text-muted);
}
.border-toggle-right:hover {
	border-color: var(--primary);
}
.border-toggle-right.border-toggle-active {
	border-color: var(--primary);
	background-color: var(--primary);
}

.border-toggle-top {
	border-left: 1px solid var(--text-muted);
	border-top: 3px solid var(--text-muted);
	border-right: 1px solid var(--text-muted);
	border-bottom: 1px solid var(--text-muted);
}
.border-toggle-top:hover {
	border-color: var(--primary);
}
.border-toggle-top.border-toggle-active {
	border-color: var(--primary);
	background-color: var(--primary);
}

.border-toggle-bottom {
	border-left: 1px solid var(--text-muted);
	border-top: 1px solid var(--text-muted);
	border-right: 1px solid var(--text-muted);
	border-bottom: 3px solid var(--text-muted);
}
.border-toggle-bottom:hover {
	border-color: var(--primary);
}
.border-toggle-bottom.border-toggle-active {
	border-color: var(--primary);
	background-color: var(--primary);
}
</style>
