<script context="module" lang="ts">
	export type SortDirection = 'asc' | 'desc' | 'none';
	
	export interface SortState {
		field: string;
		direction: SortDirection;
		initialLoad: boolean;
	}

	/**
	 * 항목 배열을 지정된 필드와 방향으로 정렬합니다.
	 * @param items 정렬할 항목 배열
	 * @param sortState 정렬 상태 객체 (field, direction, initialLoad)
	 * @returns 정렬된 항목 배열
	 */
	export function sortItems<T>(items: T[], sortState: SortState): T[] {
		// 초기 로딩 시 또는 정렬 방향이 'none'인 경우 원본 배열 반환
		if (sortState.initialLoad || sortState.direction === 'none') {
			return [...items];
		}
		
		return [...items].sort((a, b) => {
			// 필드 값 가져오기 (중첩 객체 지원)
			const valueA = getNestedValue(a, sortState.field);
			const valueB = getNestedValue(b, sortState.field);
			
			// 문자열인 경우 소문자로 변환하여 비교
			const compareA = typeof valueA === 'string' ? valueA.toLowerCase() : valueA;
			const compareB = typeof valueB === 'string' ? valueB.toLowerCase() : valueB;
			
			// 비교 가능한 값으로 변환
			const comparableA = compareA as string | number | boolean | Date;
			const comparableB = compareB as string | number | boolean | Date;
			
			// 정렬 방향에 따라 비교
			if (sortState.direction === 'asc') {
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
		change: { sortedItems: any[]; sortState: SortState };
	}>();
	
	// 정렬 상태 객체
	export let sortState: SortState = {
		field: '',
		direction: 'none',
		initialLoad: true
	};
	
	// 정렬할 항목 배열
	export let items: any[] = [];
	
	// 정렬 옵션 배열 (각 옵션은 value와 label을 가짐)
	export let options: { value: string; label: string }[] = [];
	
	// localStorage에 저장할 때 사용할 고유 키 (더 이상 사용하지 않음)
	export let storageKey: string = 'default';
	
	// 정렬된 항목 배열 (외부로 내보내기)
	export let sortedItems: any[] = [];
	
	// 정렬 상태나 항목이 변경될 때마다 정렬 적용
	// 무한 루프 방지를 위해 items나 sortState가 변경될 때만 정렬 적용
	$: if (items && items.length >= 0) {
		sortedItems = sortItems(items, sortState);
	}
	
	// 정렬된 항목이 변경될 때마다 이벤트 발생
	$: if (sortedItems) {
		dispatch('change', { sortedItems, sortState });
	}
	
	// 정렬 필드 변경 함수
	function changeSortField(field: string) {
		// 초기 로딩 상태 해제
		sortState.initialLoad = false;
		
		if (sortState.field === field) {
			// 같은 필드를 클릭한 경우 정렬 방향 순환 (asc -> desc -> none -> asc)
			if (sortState.direction === 'asc') {
				sortState.direction = 'desc';
			} else if (sortState.direction === 'desc') {
				sortState.direction = 'none';
			} else {
				sortState.direction = 'asc';
			}
		} else {
			sortState.field = field;
			sortState.direction = 'none';
		}
	}
</script>

<div class="flex items-center space-x-2 mr-2">
	<div class="text-sm text-gray-500 dark:text-gray-300">{$i18n.t('Sort by')}:</div>
	<div class="flex space-x-1">
		{#each options as option}
			<button
				class="px-2 py-1 text-xs rounded-lg {sortState.field === option.value ? 'bg-gray-100 dark:bg-gray-700' : 'hover:bg-gray-50 dark:hover:bg-gray-800'} transition"
				on:click={() => changeSortField(option.value)}
			>
				{option.label}
				{#if sortState.field === option.value}
					<span class="ml-1">
						{#if sortState.direction === 'asc'}
							<ChevronUp className="w-3 h-3 inline" />
						{:else if sortState.direction === 'desc'}
							<ChevronDown className="w-3 h-3 inline" />
						{:else}
							<span class="text-xs text-gray-400">•</span>
						{/if}
					</span>
				{/if}
			</button>
		{/each}
	</div>
</div> 