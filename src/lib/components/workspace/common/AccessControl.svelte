<script lang="ts">
	import { getContext, onMount } from 'svelte';

	const i18n = getContext('i18n');

	import { getGroups } from '$lib/apis/groups';
	import { getUsers } from '$lib/apis/users';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import UserCircleSolid from '$lib/components/icons/UserCircleSolid.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import Badge from '$lib/components/common/Badge.svelte';

	export let onChange: Function = () => {};

	export let accessRoles = ['read'];
	export let accessControl: {
		read?: {
			group_ids?: string[];
			user_ids?: string[];
		};
		write?: {
			group_ids?: string[];
			user_ids?: string[];
		};
	} | null = null;

	let selectedGroupId = '';
	let selectedUserId = '';
	let groups: any[] = [];
	let users: any[] = [];

	// 사용자 필터링 함수
	function filterAvailableUsers(users: any[], accessControlUserIds: string[] = []): any[] {
		return users.filter(user => !accessControlUserIds.includes(user.id));
	}

	onMount(async () => {
		groups = await getGroups(localStorage.token);
		const allUsers = await getUsers(localStorage.token);
		users = allUsers.filter((user: any) => user.role === 'user');

		if (accessControl === null) {
			accessControl = {
				read: {
					group_ids: [],
					user_ids: []
				},
				write: {
					group_ids: [],
					user_ids: []
				}
			};
		} else {
			accessControl = {
				read: {
					group_ids: accessControl?.read?.group_ids ?? [],
					user_ids: accessControl?.read?.user_ids ?? []
				},
				write: {
					group_ids: accessControl?.write?.group_ids ?? [],
					user_ids: accessControl?.write?.user_ids ?? []
				}
			};
		}
	});

	$: if (selectedGroupId) {
		onSelectGroup();
	}

	$: if (selectedUserId && selectedUserId !== '') {
		onSelectUser();
	}

	const onSelectGroup = () => {
		if (selectedGroupId !== '' && accessControl) {
			// read 권한에 추가
			if (accessControl.read) {
				accessControl.read.group_ids = [...accessControl.read.group_ids || [], selectedGroupId];
			}
			
			if (accessControl.write) {
				accessControl.write.group_ids = [...accessControl.write.group_ids || [], selectedGroupId];
			}
			
			selectedGroupId = '';
			accessControl = { ...accessControl };
			onChange(accessControl);
		}
	};

	const onSelectUser = () => {
		if (selectedUserId !== '' && accessControl) {
			// read 권한에 추가
			if (accessControl.read) {
				accessControl.read.user_ids = [...accessControl.read.user_ids || [], selectedUserId];
			}
			
			if (accessControl.write) {
				accessControl.write.user_ids = [...accessControl.write.user_ids || [], selectedUserId];
			}
			
			selectedUserId = '';
			accessControl = { ...accessControl };
			onChange(accessControl);
		}
	};

	// 사용자 제거
	function onRemoveUser(userId: string) {
		if (accessControl) {
			// write 권한에서 제거
			if (accessControl.write) {
				accessControl.write.user_ids = accessControl.write.user_ids?.filter(
					(id) => id !== userId
				) || [];
			}
			
			// read 권한에서도 제거
			if (accessControl.read) {
				accessControl.read.user_ids = accessControl.read.user_ids?.filter(
					(id) => id !== userId
				) || [];
			}
			
			// 강제로 UI 업데이트 트리거
			accessControl = { ...accessControl };
			// 변경사항 저장
			onChange(accessControl);
		}
	}
</script>

<div class="rounded-lg flex flex-col gap-2">
	<div class="">
		<div class="flex gap-2.5 items-center mb-1">
			<div>
				<div class="p-2 bg-black/5 dark:bg-white/5 rounded-full">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="1.5"
						stroke="currentColor"
						class="w-5 h-5"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"
						/>
					</svg>
				</div>
			</div>

			<div>
				<div class="text-sm font-medium">
					Private
				</div>
				<div class="text-xs text-gray-400 font-medium">
					{$i18n.t('Only select users and groups with permission can access')}
				</div>
			</div>
		</div>
	</div>
	
	<!-- 그룹 권한 관리 섹션 -->
	<div>
		<div class="">
			<div class="flex justify-between mb-1.5">
				<div class="text-sm font-semibold">
					{$i18n.t('Groups')}
				</div>
			</div>

			<div class="mb-1">
				<div class="flex w-full">
					<div class="flex flex-1 items-center">
						<div class="w-full px-0.5">
							<select
								class="outline-hidden bg-transparent text-sm rounded-lg block w-full pr-10 max-w-full
								{selectedGroupId ? 'text-gray-900 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400'}
								dark:placeholder-gray-500 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
								bind:value={selectedGroupId}
							>
								<option class="text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800" value="" disabled selected
									>{$i18n.t('Select a group')}</option
								>
								{#each groups.filter((group) => !accessControl?.write?.group_ids?.includes(group.id)) as group}
									<option class="text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800" value={group.id}>{group.name}</option>
								{/each}
							</select>
						</div>
					</div>
				</div>
			</div>

			<hr class="border-gray-100 dark:border-gray-700/10 mt-1.5 mb-2.5 w-full" />

			<div class="flex flex-col gap-2 mb-1 px-0.5">
				{#if groups.filter((group) => accessControl?.write?.group_ids?.includes(group.id) || false).length > 0}
					{#each groups.filter((group) => accessControl?.write?.group_ids?.includes(group.id) || false) as group}
						<div class="flex items-center gap-3 justify-between text-xs w-full transition">
							<div class="flex items-center gap-1.5 w-full font-medium">
								<div>
									<UserCircleSolid className="size-4" />
								</div>

								<div>
									{group.name}
								</div>
							</div>

							<div class="w-full flex justify-end items-center gap-0.5">
								<button
									class="rounded-full p-1 hover:bg-blue-400 dark:hover:bg-gray-800 hover:text-white transition-colors"
									type="button"
									on:click={() => {
										if (accessRoles.includes('write') && accessControl) {
											if (accessControl.write?.group_ids?.includes(group.id)) {
												accessControl.write.group_ids = accessControl.write.group_ids?.filter(
													(group_id) => group_id !== group.id
												) || [];
											} else if (accessControl.write) {
												accessControl.write.group_ids = [
													...(accessControl.write?.group_ids || []),
													group.id
												];
											}
											accessControl = { ...accessControl };
											onChange(accessControl);
										}
									}}
								>
									{#if accessControl && accessControl.write?.group_ids?.includes(group.id)}
										<Badge type={'success'} content={$i18n.t('Write')} />
									{:else}
										<Badge type={'info'} content={$i18n.t('Read')} />
									{/if}
								</button>

								<button
									class="rounded-full p-1 hover:bg-blue-400 dark:hover:bg-gray-800 hover:text-white transition-colors"
									type="button"
									on:click={() => {
										if (accessControl) {
											if (accessControl.write) {
												accessControl.write.group_ids = accessControl.write.group_ids?.filter(
													(id) => id !== group.id
												) || [];
											}
											
											if (accessControl.read) {
												accessControl.read.group_ids = accessControl.read.group_ids?.filter(
													(id) => id !== group.id
												) || [];
											}
											
											accessControl = { ...accessControl };
											onChange(accessControl);
										}
									}}
								>
									<XMark />
								</button>
							</div>
						</div>
					{/each}
					
				{/if}
			</div>
		</div>
	</div>
	
	<div class="mt-4 border-t pt-3 border-gray-100 dark:border-gray-700/10">
		<div class="flex justify-between mb-1.5">
			<div class="text-sm font-semibold">
				{$i18n.t('Users')}
			</div>
		</div>
		
		<div class="mb-1">
			<div class="flex w-full">
				<div class="flex flex-1 items-center">
					<div class="w-full px-0.5">
						<select
							class="outline-hidden bg-transparent text-sm rounded-lg block w-full pr-10 max-w-full
							{selectedUserId ? 'text-gray-900 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400'}
							dark:placeholder-gray-500 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
							bind:value={selectedUserId}
						>
							<option class="text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800" value="" disabled selected
								>{$i18n.t('Select a user')}</option
							>
							{#each filterAvailableUsers(users, accessControl?.write?.user_ids || []) as user}
								<option class="text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800" value={user.id}>{user.name}</option>
							{/each}
						</select>
					</div>
				</div>
			</div>
		</div>
		
		<hr class="border-gray-100 dark:border-gray-700/10 mt-1.5 mb-2.5 w-full" />
		
		<div class="flex flex-col gap-2 mb-1 px-0.5">
			{#if accessControl && accessControl.write}
				{#each users.filter(user => accessControl?.write?.user_ids?.includes(user.id)) as user}
					<div class="flex items-center gap-3 justify-between text-xs w-full transition">
						<div class="flex items-center gap-1.5 w-full font-medium">
							<div>
								<UserCircleSolid className="size-4" />
							</div>

							<div>
								{user.name}
							</div>
						</div>

						<div class="w-full flex justify-end items-center gap-0.5">
							{#if accessRoles.includes('write') && accessControl.write}
								<button
									class="rounded-full p-1 hover:bg-blue-400 dark:hover:bg-gray-800 hover:text-white transition-colors"
									type="button"
									on:click={() => {
										if (accessControl && accessControl.write) {
											if (accessControl.write?.user_ids?.includes(user.id)) {
												accessControl.write.user_ids = accessControl.write.user_ids?.filter(
													(userId) => userId !== user.id
												) || [];
											} else {
												accessControl.write.user_ids = [
													...(accessControl.write?.user_ids || []),
													user.id
												];
											}
											accessControl = { ...accessControl };
											onChange(accessControl);
										}
									}}
								>
									{#if accessControl.write?.user_ids?.includes(user.id)}
										<Badge type={'success'} content={$i18n.t('Write')} />
									{:else}
										<Badge type={'info'} content={$i18n.t('Read')} />
									{/if}
								</button>
							{/if}

							<button
								class="rounded-full p-1 hover:bg-blue-400 dark:hover:bg-gray-800 hover:text-white transition-colors"
								type="button"
								on:click={() => onRemoveUser(user.id)}
							>
								<XMark />
							</button>
						</div>
					</div>
				{/each}
			{/if}
		</div>
	</div>
</div>
