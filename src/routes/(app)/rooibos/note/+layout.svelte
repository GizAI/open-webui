<!-- layout.svelte -->
<script lang="ts">
	import { getContext } from 'svelte';
	import { WEBUI_NAME,showSidebar} from '$lib/stores';

	const i18n = getContext('i18n');
</script>

<svelte:head>
	<title>
		{$i18n.t('Workspace')}  | {$WEBUI_NAME}
	</title>
</svelte:head>

<div
	class=" relative flex flex-col w-full h-screen max-h-[100dvh] {$showSidebar
		? 'md:max-w-[calc(100%-260px)]'
		: ''}"
>
	<div class="  pb-1 px-[18px] flex-1 max-h-full overflow-y-auto" id="workspace-container">
		<slot />
	</div>
</div>

