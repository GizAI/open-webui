<script lang="ts">
	import { getContext } from 'svelte';
	const i18n = getContext('i18n');

	import Modal from '$lib/components/common/Modal.svelte';
	import RooibosAccessControl from './RooibosAccessControl.svelte';

	type AccessControlConfig = {
		read?: {
			group_ids: string[];
			user_ids: string[];
		};
		write?: {
			group_ids: string[];
			user_ids: string[];
		};
	};

	export let show = false;
	export let accessControl: AccessControlConfig | null = null;
	export let accessRoles: string[] = ['read'];

	export let onChange: Function = () => {};
</script>

<Modal size="sm" bind:show>
	<div>
		<div class="flex justify-between dark:text-gray-100 px-5 pt-3 pb-1">
			<div class="text-lg font-medium self-center font-primary">
				{$i18n.t('사용자 공유')}
			</div>
			<button
				class="self-center"
				on:click={() => {
					show = false;
				}}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="w-5 h-5"
				>
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>

		<div class="w-full px-5 pb-4 dark:text-white">
			<RooibosAccessControl bind:accessControl {onChange} {accessRoles} />
		</div>
	</div>
</Modal> 