<template>
	<div class="menu" v-if="typeof index == 'number'" :style="{ top, left }" ref="DOMRef">
		<!-- Table-level menu (index === -1) -->
		<ul v-if="index === -1" class="menu-list">
			<li class="menu-item">
				<button
					class="menu-button menu-button delete-btn"
					@click="$emit('handleMenuClick', -1, 'deleteTable')"
				>
					<svg
						width="16"
						height="16"
						viewBox="0 0 16 16"
						fill="none"
						xmlns="http://www.w3.org/2000/svg"
					>
						<path
							d="M2 4H14M5.33331 4V2.66667C5.33331 2.31305 5.47379 1.97391 5.72385 1.72385C5.97391 1.47379 6.31305 1.33333 6.66665 1.33333H9.33331C9.68692 1.33333 10.0261 1.47379 10.2761 1.72385C10.5261 1.97391 10.6666 2.31305 10.6666 2.66667V4M12.6666 4V13.3333C12.6666 13.6869 12.5261 14.0261 12.2761 14.2761C12.0261 14.5261 11.6869 14.6667 11.3333 14.6667H4.66665C4.31305 14.6667 3.97391 14.5261 3.72385 14.2761C3.47379 14.0261 3.33331 13.6869 3.33331 13.3333V4H12.6666Z"
							stroke="currentColor"
							stroke-linecap="round"
							stroke-linejoin="round"
						/>
					</svg>
					<span>Delete Table</span>
				</button>
			</li>
		</ul>

		<!-- Column-level menu (index >= 0) -->
		<template v-else>
			<ul class="menu-list">
				<span class="menu-title">
					<i class="fa fa-columns" aria-hidden="true"></i>
					Insert Column
				</span>
				<hr />
				<li class="menu-item">
					<button class="menu-button" @click="$emit('handleMenuClick', index, 'before')">
						<svg
							width="16"
							height="16"
							viewBox="0 0 16 16"
							fill="none"
							xmlns="http://www.w3.org/2000/svg"
						>
							<path
								d="M4.2666 7.99778L12.2666 8"
								stroke="#525252"
								stroke-linecap="round"
								stroke-linejoin="round"
							/>
							<path
								d="M7.2002 11.5535L3.64464 7.99791L7.2002 4.44236"
								stroke="#525252"
								stroke-linecap="round"
								stroke-linejoin="round"
							/>
						</svg>

						<span>Insert Left</span>
					</button>
				</li>
				<li class="menu-item">
					<button class="menu-button" @click="$emit('handleMenuClick', index, 'after')">
						<svg
							width="16"
							height="16"
							viewBox="0 0 16 16"
							fill="none"
							xmlns="http://www.w3.org/2000/svg"
						>
							<path
								d="M11.7334 8.00222L3.7334 8"
								stroke="#383838"
								stroke-linecap="round"
								stroke-linejoin="round"
							/>
							<path
								d="M8.7998 4.44653L12.3554 8.00209L8.7998 11.5576"
								stroke="#383838"
								stroke-linecap="round"
								stroke-linejoin="round"
							/>
						</svg>

						<span>Insert Right</span>
					</button>
				</li>
			</ul>
			<ul class="menu-list">
				<li class="menu-item">
					<button
						class="menu-button menu-button delete-btn"
						@click="$emit('handleMenuClick', index, 'delete')"
					>
						Delete
					</button>
				</li>
			</ul>
		</template>
	</div>
</template>

<script setup>
import { ref, toRefs } from "vue";
import { onClickOutside } from "@vueuse/core";
const props = defineProps({
	menu: {
		type: Object,
		required: true,
	},
});
const emit = defineEmits(["handleMenuClick", "close"]);
const DOMRef = ref(null);
const { left, top, index } = toRefs(props.menu);
onClickOutside(DOMRef, () => {
	if (props.menu.index === -1) {
		emit("close");
	} else {
		props.menu.index = null;
	}
});
</script>

<style lang="scss" scoped>
.menu {
	position: absolute;
	display: flex;
	flex-direction: column;
	background-color: var(--fg-color);
	border-radius: 10px;
	border: 1px solid var(--dark-border-color);
	box-shadow: 0px 2px 10px 1px rgb(0 0 0 / 15%);
	z-index: 9999;
}
.menu-list {
	margin: 0;
	display: block;
	width: 100%;
	min-width: 160px;
	padding: 8px;
	list-style: none;
	& + .menu-list {
		border-top: 1px solid var(--dark-border-color);
	}
	.menu-title {
		padding: 8px;
		font-weight: 500;
		i {
			margin-right: 5px;
			font-size: 0.85rem;
		}
	}
}
.menu-item {
	position: relative;
	padding-left: 5px;
	min-height: 36px;
}
.delete-btn:hover {
	color: var(--danger);
}
.menu-button {
	font: inherit;
	border: 0;
	padding: 5px 8px;
	padding-right: 24px;
	width: 100%;
	border-radius: 8px;
	text-align: left;
	display: flex;
	align-items: center;
	position: relative;
	background-color: var(--fg-color);
	&:hover {
		background-color: var(--gray-100);
	}
	&:active,
	&:focus {
		background-color: var(--gray-100);
		outline: unset;
		border-style: inset;
	}
	span {
		padding-left: 5px;
	}
}
</style>
