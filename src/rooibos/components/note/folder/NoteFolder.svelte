<!--NoteFolder.svelte-->
<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import Collapsible from '$lib/components/common/Collapsible.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import ChevronRight from '$lib/components/icons/ChevronRight.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';

	const dispatch = createEventDispatcher();

	export let open: boolean = true;
	export let name: string = '';
	export let collapsible: boolean = true;
	export let onAdd: null | Function = null;
	export let onAddLabel: string = '새페이지';
	export let className: string = '';

	const addPage = (e: Event) => {
		e.stopPropagation();
		if (onAdd) onAdd();
	};
</script>

<div class={className}>
	{#if collapsible}
		<Collapsible
			bind:open
			className="w-full"
			buttonClassName="w-full"
			on:change={(e) => dispatch('change', e.detail)}
		>
			<div class="w-full group flex items-center justify-between hover:bg-gray-100 dark:hover:bg-gray-900 transition py-1 px-2">
				<button
					class="flex items-center gap-1 text-xs font-medium w-full"
					on:click={() => dispatch('toggle')}
				>
					{#if open}
						<ChevronDown className="size-3" strokeWidth="2.5" />
					{:else}
						<ChevronRight className="size-3" strokeWidth="2.5" />
					{/if}
					<span>{name}</span>
				</button>

				{#if onAdd}
					<button class="invisible group-hover:visible" on:click={addPage}>
						<Tooltip content={onAddLabel}>
							<Plus className="size-3" strokeWidth="2.5" />
						</Tooltip>
					</button>
				{/if}
			</div>

			<div slot="content">
				<slot></slot>
			</div>
		</Collapsible>
	{:else}
		<div class="flex items-center justify-between py-1 px-2 hover:bg-gray-100 dark:hover:bg-gray-900 transition">
			<span>{name}</span>
			{#if onAdd}
				<button on:click={addPage}>
					<Tooltip content={onAddLabel}>
						<Plus className="size-3" strokeWidth="2.5" />
					</Tooltip>
				</button>
			{/if}
		</div>
		<slot></slot>
	{/if}
</div>

