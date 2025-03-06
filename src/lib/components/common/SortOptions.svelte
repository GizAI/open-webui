<script context="module" lang="ts">
	export type SortDirection = 'asc' | 'desc';

	/**
	 * 항목 배열을 지정된 필드와 방향으로 정렬합니다.
	 * @param items 정렬할 항목 배열
	 * @param field 정렬 기준 필드
	 * @param direction 정렬 방향 ('asc' 또는 'desc')
	 * @returns 정렬된 항목 배열
	 */
	export function sortItems<T>(items: T[], field: string, direction: SortDirection): T[] {
		return [...items].sort((a, b) => {
			// 필드 값 가져오기 (중첩 객체 지원)
			const valueA = getNestedValue(a, field);
			const valueB = getNestedValue(b, field);
			
			// 문자열인 경우 소문자로 변환하여 비교
			const compareA = typeof valueA === 'string' ? valueA.toLowerCase() : valueA;
			const compareB = typeof valueB === 'string' ? valueB.toLowerCase() : valueB;
			
			// 비교 가능한 값으로 변환
			const comparableA = compareA as string | number | boolean | Date;
			const comparableB = compareB as string | number | boolean | Date;
			
			// 정렬 방향에 따라 비교
			if (direction === 'asc') {
				return comparableA > comparableB ? 1 : comparableA < comparableB ? -1 : 0;
			} else {
				return comparableA < comparableB ? 1 : comparableA > comparableB ? -1 : 0;
			}
		});
	}

	/**
	 * 객체에서 중첩된 필드 값을 가져옵니다.
	 * 예: getNestedValue(obj, 'user.name')
	 * @param obj 대상 객체
	 * @param path 필드 경로 (점으로 구분)
	 * @returns 필드 값
	 */
	function getNestedValue(obj: unknown, path: string): unknown {
		// 기본값 설정
		if (!obj) return '';
		if (!path) return obj;
		
		// 점으로 구분된 경로를 배열로 변환
		const keys = path.split('.');
		let value = obj as Record<string, unknown>;
		
		// 중첩 객체 탐색
		for (const key of keys) {
			if (value === null || value === undefined || typeof value !== 'object') {
				return '';
			}
			value = value[key] as Record<string, unknown>;
		}
		
		// undefined나 null인 경우 빈 문자열 반환
		return value === null || value === undefined ? '' : value;
	}
</script>

<script lang="ts">
	import ChevronDown from '../icons/ChevronDown.svelte';
	import ChevronUp from '../icons/ChevronUp.svelte';
	import { getContext, createEventDispatcher } from 'svelte';
	import type { Readable } from 'svelte/store';
	
	// i18n을 Readable 스토어 타입으로 지정
	interface I18nStore extends Readable<{
		t: (key: string) => string;
	}> {}
	
	const i18n = getContext<I18nStore>('i18n');
	const dispatch = createEventDispatcher<{
		change: { field: string; direction: SortDirection };
	}>();
	
	// 정렬 필드 타입 (제네릭으로 받아서 사용)
	export let sortField: string;
	export let sortDirection: SortDirection = 'asc';
	
	// 정렬 옵션 배열 (각 옵션은 value와 label을 가짐)
	export let options: { value: string; label: string }[] = [];
	
	// 정렬 필드 변경 함수
	function changeSortField(field: string) {
		if (sortField === field) {
			// 같은 필드를 클릭한 경우 정렬 방향 전환
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			// 다른 필드를 클릭한 경우 해당 필드로 변경하고 오름차순으로 설정
			sortField = field;
			sortDirection = 'asc';
		}
		
		// 변경 이벤트 발생
		dispatch('change', { field: sortField, direction: sortDirection });
	}
</script>

<div class="flex items-center space-x-2 mr-2">
	<div class="text-sm text-gray-500 dark:text-gray-300">{$i18n.t('Sort by')}:</div>
	<div class="flex space-x-1">
		{#each options as option}
			<button
				class="px-2 py-1 text-xs rounded-lg {sortField === option.value ? 'bg-gray-100 dark:bg-gray-700' : 'hover:bg-gray-50 dark:hover:bg-gray-800'} transition"
				on:click={() => changeSortField(option.value)}
			>
				{option.label}
				{#if sortField === option.value}
					<span class="ml-1">
						{#if sortDirection === 'asc'}
							<ChevronUp className="w-3 h-3 inline" />
						{:else}
							<ChevronDown className="w-3 h-3 inline" />
						{/if}
					</span>
				{/if}
			</button>
		{/each}
	</div>
</div> 