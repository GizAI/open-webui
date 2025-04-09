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

<div class="relative {className}">
	{#if collapsible}
		<Collapsible
			bind:open
			className="w-full"
			buttonClassName="w-full"
			on:change={(e) => dispatch('change', e.detail)}
		>
			<!-- svelte-ignore a11y-no-static-element-interactions -->
			<div class="w-full group rounded-md relative flex items-center justify-between hover:bg-gray-100 dark:hover:bg-gray-900 text-gray-800 dark:text-gray-200 transition">
				<button class="w-full py-1.5 pl-2 flex items-center gap-1.5 text-sm font-medium">
					<div class="text-gray-300 dark:text-gray-600">
						{#if open}
							<ChevronDown className="size-3" strokeWidth="2.5" />
						{:else}
							<ChevronRight className="size-3" strokeWidth="2.5" />
						{/if}
					</div>

					<div class="translate-y-[0.5px]">
						{name}
					</div>
				</button>

				{#if onAdd}
					<button
						class="absolute z-10 right-2 invisible group-hover:visible self-center flex items-center dark:text-gray-300"
						on:pointerup={(e) => e.stopPropagation()}
						on:click={addPage}
					>
						<Tooltip content={onAddLabel}>
							<button class="p-0.5 dark:hover:bg-gray-850 rounded-lg touch-auto">
								<Plus className="size-3" strokeWidth="2.5" />
							</button>
						</Tooltip>
					</button>
				{/if}
			</div>

			<div slot="content" class="w-full">
				<slot></slot>
			</div>
		</Collapsible>
	{:else}
		<div class="w-full group rounded-md relative flex items-center justify-between hover:bg-gray-100 dark:hover:bg-gray-900 text-gray-500 dark:text-gray-500 transition py-1.5 pl-2">
			<span class="text-xs font-medium">{name}</span>
			{#if onAdd}
				<button
					class="absolute z-10 right-2 invisible group-hover:visible self-center flex items-center dark:text-gray-300"
					on:click={addPage}
				>
					<Tooltip content={onAddLabel}>
						<button class="p-0.5 dark:hover:bg-gray-850 rounded-lg touch-auto">
							<Plus className="size-3" strokeWidth="2.5" />
						</button>
					</Tooltip>
				</button>
			{/if}
		</div>
		<slot></slot>
	{/if}
</div>

