<script lang="ts">
	import { chatId, mobile, showSidebar } from '$lib/stores';
	
	// 외부에서 selectedChatId를 받아오기 위한 export 변수 선언
	export let selectedChatId: string | null = null;
</script>

<div class="px-1.5 flex justify-center text-gray-800 dark:text-gray-200">
	<a
		class="flex-grow flex space-x-3 rounded-lg px-2 py-[7px] hover:bg-gray-100 dark:hover:bg-gray-900 transition"
		href="/rooibos/corpsearch"
		on:click={() => {
			selectedChatId = null;
			chatId.set('');
			if ($mobile) {
				showSidebar.set(false);
			}
		}}
		draggable="false"
	>
		<div class="self-center">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke-width="2"
				stroke="currentColor"
				class="size-[1.1rem]"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21"
				/>
			</svg>
		</div>
		<div class="flex self-center">
			<div class="self-center font-medium text-sm font-primary">기업 찾기</div>
		</div>
	</a>
</div> 