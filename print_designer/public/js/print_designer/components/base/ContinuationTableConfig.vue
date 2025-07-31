<template>
	<div class="continuation-config-panel">
		<div class="config-header">
			<h4>Continuation Table Settings</h4>
			<div class="enable-toggle">
				<input
					type="checkbox"
					id="enable-continuation"
					v-model="localConfig.enabled"
					@change="updateConfig"
				/>
				<label for="enable-continuation">Enable Table Continuation</label>
			</div>
		</div>

		<div v-if="localConfig.enabled" class="config-content">
			<!-- Mode Selection -->
			<div class="config-section">
				<h5>Continuation Mode</h5>
				<div class="mode-selection">
					<div class="mode-option">
						<input
							type="radio"
							id="mode-before"
							value="before"
							v-model="localConfig.mode"
							@change="updateConfig"
						/>
						<label for="mode-before" class="mode-label">
							<div class="mode-title">Before (Separate Tables)</div>
							<div class="mode-description">Creates separate complete tables per page, like multiple invoices</div>
						</label>
					</div>
					<div class="mode-option">
						<input
							type="radio"
							id="mode-after"
							value="after"
							v-model="localConfig.mode"
							@change="updateConfig"
						/>
						<label for="mode-after" class="mode-label">
							<div class="mode-title">After (Continuation Table)</div>
							<div class="mode-description">Single continuous table with balance forward and running totals</div>
						</label>
					</div>
				</div>
			</div>

			<!-- Basic Settings -->
			<div class="config-section">
				<h5>Basic Settings</h5>
				
				<div class="form-group">
					<label for="rows-per-page">Rows per Page:</label>
					<input
						type="number"
						id="rows-per-page"
						v-model.number="localConfig.rowsPerPage"
						min="1"
						max="50"
						@change="updateConfig"
						class="form-control"
					/>
				</div>

				<div class="form-group">
					<label for="min-rows-display">Minimum Rows Display:</label>
					<input
						type="number"
						id="min-rows-display"
						v-model.number="localConfig.minRowsDisplay"
						min="1"
						max="50"
						@change="updateConfig"
						class="form-control"
					/>
					<small class="form-text">Empty rows will be shown to reach this minimum</small>
				</div>

				<div class="checkbox-group">
					<div class="checkbox-item">
						<input
							type="checkbox"
							id="use-fixed-height"
							v-model="localConfig.useFixedHeight"
							@change="updateConfig"
						/>
						<label for="use-fixed-height">Use Fixed Height</label>
					</div>

					<div class="checkbox-item">
						<input
							type="checkbox"
							id="show-empty-rows"
							v-model="localConfig.showEmptyRows"
							@change="updateConfig"
						/>
						<label for="show-empty-rows">Show Empty Rows</label>
					</div>

					<div class="checkbox-item">
						<input
							type="checkbox"
							id="show-running-totals"
							v-model="localConfig.showRunningTotals"
							@change="updateConfig"
						/>
						<label for="show-running-totals">Show Running Totals</label>
					</div>

					<div class="checkbox-item">
						<input
							type="checkbox"
							id="show-balance-forward"
							v-model="localConfig.showBalanceForward"
							@change="updateConfig"
						/>
						<label for="show-balance-forward">Show Balance Forward</label>
					</div>
				</div>
			</div>

			<!-- Total Columns Selection -->
			<div class="config-section" v-if="localConfig.showRunningTotals">
				<h5>Total Columns</h5>
				<div class="columns-selection">
					<div
						v-for="column in availableColumns"
						:key="column.fieldname"
						class="column-checkbox"
					>
						<input
							type="checkbox"
							:id="`total-col-${column.fieldname}`"
							:value="column.fieldname"
							v-model="localConfig.totalColumns"
							@change="updateConfig"
						/>
						<label :for="`total-col-${column.fieldname}`">
							{{ column.label || column.fieldname }}
						</label>
					</div>
				</div>
			</div>

			<!-- Headers and Footers -->
			<div class="config-section">
				<h5>Continuation Messages</h5>
				
				<div class="form-group">
					<label for="continuation-header">Continuation Header:</label>
					<input
						type="text"
						id="continuation-header"
						v-model="localConfig.continuationHeader"
						@change="updateConfig"
						class="form-control"
						placeholder="Continued from previous page"
					/>
				</div>

				<div class="form-group">
					<label for="continuation-footer">Continuation Footer:</label>
					<input
						type="text"
						id="continuation-footer"
						v-model="localConfig.continuationFooter"
						@change="updateConfig"
						class="form-control"
						placeholder="Continued on next page"
					/>
				</div>
			</div>

			<!-- Preview -->
			<div class="config-section">
				<h5>Preview</h5>
				<div class="preview-info">
					<div v-if="previewData.success" class="preview-stats">
						<div class="stat">
							<span class="label">Total Rows:</span>
							<span class="value">{{ previewData.total_rows }}</span>
						</div>
						<div class="stat">
							<span class="label">Total Pages:</span>
							<span class="value">{{ previewData.total_pages }}</span>
						</div>
						<div class="stat">
							<span class="label">Rows per Page:</span>
							<span class="value">{{ previewData.rows_per_page }}</span>
						</div>
					</div>
					<div v-else-if="previewData.error" class="preview-error">
						<i class="fa fa-exclamation-triangle"></i>
						{{ previewData.error }}
					</div>
					<div v-else class="preview-loading">
						<i class="fa fa-spinner fa-spin"></i>
						Loading preview...
					</div>
				</div>
				
				<button
					type="button"
					class="btn btn-sm btn-secondary"
					@click="refreshPreview"
					:disabled="!table || !table.fieldname"
				>
					<i class="fa fa-refresh"></i>
					Refresh Preview
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue';
import { useMainStore } from '../../store/MainStore';

const MainStore = useMainStore();

const props = defineProps({
	element: {
		type: Object,
		required: true
	}
});

const emit = defineEmits(['update-config']);

// Local config state
const localConfig = ref({
	enabled: false,
	mode: "before",  // "before" or "after" - using "before" as default per user request
	rowsPerPage: 10,
	minRowsDisplay: 10,  // Minimum rows to display
	useFixedHeight: true,  // Use fixed table height
	showEmptyRows: true,  // Show empty rows to fill minimum
	showRunningTotals: true,
	showBalanceForward: true,
	continuationHeader: "Continued from previous page",
	continuationFooter: "Continued on next page",
	totalColumns: [],
	pageNumbering: true,
	showPageTotals: true
});

// Preview data
const previewData = ref({
	success: false,
	total_rows: 0,
	total_pages: 0,
	rows_per_page: 10,
	pages: [],
	error: null
});

// Computed properties
const table = computed(() => props.element.table);

const availableColumns = computed(() => {
	if (!props.element.columns) return [];
	
	// Filter columns that might contain numeric data
	return props.element.columns.filter(column => {
		const fieldname = column.fieldname;
		if (!fieldname) return false;
		
		// Common patterns for numeric fields
		const numericPatterns = [
			/amount/i, /total/i, /rate/i, /price/i, /cost/i,
			/qty/i, /quantity/i, /weight/i, /value/i,
			/tax/i, /discount/i, /charge/i, /fee/i
		];
		
		return numericPatterns.some(pattern => pattern.test(fieldname));
	});
});

// Initialize config from element
onMounted(() => {
	if (props.element.continuationConfig) {
		Object.assign(localConfig.value, props.element.continuationConfig);
	}
	refreshPreview();
});

// Watch for changes in element
watch(() => props.element.continuationConfig, (newConfig) => {
	if (newConfig) {
		Object.assign(localConfig.value, newConfig);
	}
}, { deep: true });

// Methods
const updateConfig = () => {
	// Validate config
	if (localConfig.value.rowsPerPage < 1) {
		localConfig.value.rowsPerPage = 1;
	}
	if (localConfig.value.rowsPerPage > 50) {
		localConfig.value.rowsPerPage = 50;
	}
	
	// Update element config
	props.element.continuationConfig = { ...localConfig.value };
	
	// Emit update
	emit('update-config', localConfig.value);
	
	// Refresh preview if enabled
	if (localConfig.value.enabled) {
		refreshPreview();
	}
};

const refreshPreview = async () => {
	if (!table.value || !table.value.fieldname) {
		previewData.value = {
			success: false,
			error: "No table selected or table has no fieldname"
		};
		return;
	}
	
	try {
		previewData.value = { success: false, error: null };
		
		const response = await frappe.call({
			method: "print_designer.custom.continuation_table_utils.get_table_data_preview",
			args: {
				doctype: MainStore.doctype,
				docname: MainStore.docname || "new-doc",
				fieldname: table.value.fieldname,
				rows_per_page: localConfig.value.rowsPerPage
			}
		});
		
		if (response.message.success) {
			previewData.value = response.message;
		} else {
			previewData.value = {
				success: false,
				error: response.message.error || "Unknown error occurred"
			};
		}
	} catch (error) {
		previewData.value = {
			success: false,
			error: error.message || "Failed to load preview"
		};
	}
};

// Auto-refresh preview when rows per page changes
watch(() => localConfig.value.rowsPerPage, () => {
	if (localConfig.value.enabled) {
		refreshPreview();
	}
});
</script>

<style lang="scss" scoped>
.continuation-config-panel {
	background: #f8f9fa;
	border: 1px solid #dee2e6;
	border-radius: 6px;
	padding: 16px;
	margin: 12px 0;
	
	.config-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 16px;
		padding-bottom: 12px;
		border-bottom: 1px solid #dee2e6;
		
		h4 {
			margin: 0;
			color: #495057;
			font-size: 1.1rem;
		}
		
		.enable-toggle {
			display: flex;
			align-items: center;
			gap: 8px;
			
			input[type="checkbox"] {
				transform: scale(1.2);
			}
			
			label {
				font-weight: 500;
				color: #6c757d;
				margin: 0;
			}
		}
	}
	
	.config-content {
		.config-section {
			margin-bottom: 20px;
			
			h5 {
				color: #495057;
				font-size: 0.95rem;
				font-weight: 600;
				margin-bottom: 12px;
				padding-bottom: 4px;
				border-bottom: 1px solid #e9ecef;
			}
			
			.form-group {
				margin-bottom: 12px;
				
				label {
					display: block;
					font-weight: 500;
					color: #6c757d;
					margin-bottom: 4px;
					font-size: 0.9rem;
				}
				
				.form-control {
					width: 100%;
					padding: 6px 10px;
					border: 1px solid #ced4da;
					border-radius: 4px;
					font-size: 0.9rem;
					
					&:focus {
						outline: none;
						border-color: #007bff;
						box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
					}
				}
			}
			
			.checkbox-group {
				display: flex;
				flex-direction: column;
				gap: 8px;
				
				.checkbox-item {
					display: flex;
					align-items: center;
					gap: 8px;
					
					input[type="checkbox"] {
						transform: scale(1.1);
					}
					
					label {
						margin: 0;
						font-size: 0.9rem;
						color: #6c757d;
					}
				}
			}
			
			.columns-selection {
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
				gap: 8px;
				
				.column-checkbox {
					display: flex;
					align-items: center;
					gap: 6px;
					padding: 6px;
					background: white;
					border: 1px solid #e9ecef;
					border-radius: 4px;
					
					input[type="checkbox"] {
						transform: scale(1.05);
					}
					
					label {
						margin: 0;
						font-size: 0.85rem;
						color: #495057;
						flex: 1;
					}
				}
			}
		}
		
		.preview-info {
			background: white;
			border: 1px solid #e9ecef;
			border-radius: 4px;
			padding: 12px;
			margin-bottom: 12px;
			
			.preview-stats {
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
				gap: 12px;
				
				.stat {
					display: flex;
					flex-direction: column;
					align-items: center;
					text-align: center;
					
					.label {
						font-size: 0.8rem;
						color: #6c757d;
						margin-bottom: 4px;
					}
					
					.value {
						font-size: 1.2rem;
						font-weight: 600;
						color: #007bff;
					}
				}
			}
			
			.preview-error {
				color: #dc3545;
				display: flex;
				align-items: center;
				gap: 8px;
				font-size: 0.9rem;
			}
			
			.preview-loading {
				color: #6c757d;
				display: flex;
				align-items: center;
				gap: 8px;
				font-size: 0.9rem;
			}
		}
		
		.btn {
			padding: 6px 12px;
			border: 1px solid #ced4da;
			border-radius: 4px;
			background: white;
			color: #495057;
			font-size: 0.85rem;
			cursor: pointer;
			display: inline-flex;
			align-items: center;
			gap: 6px;
			
			&:hover:not(:disabled) {
				background: #f8f9fa;
				border-color: #adb5bd;
			}
			
			&:disabled {
				opacity: 0.6;
				cursor: not-allowed;
			}
			
			i {
				font-size: 0.8rem;
			}
		}
	}
}
</style>