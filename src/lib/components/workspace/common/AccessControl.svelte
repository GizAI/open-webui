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
	let isPublic = false;

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
		
		// Public 모드 여부 초기화
		isPublic = accessControl.read?.user_ids?.length === 0 && 
				   accessControl.read?.group_ids?.length === 0 && 
				   accessControl.write?.user_ids?.length === 0 && 
				   accessControl.write?.group_ids?.length === 0;
	});

	$: if (selectedGroupId) {
		onSelectGroup();
	}

	$: if (selectedUserId && selectedUserId !== '') {
		onSelectUser();
	}

	const onSelectGroup = () => {
		if (selectedGroupId !== '' && accessControl) {
			// Public 모드에서 그룹을 추가하면 Private 모드로 전환
			isPublic = false;
			
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
			// Public 모드에서 사용자를 추가하면 Private 모드로 전환
			isPublic = false;
			
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
				);
			}
			
			// read 권한에서도 제거
			if (accessControl.read) {
				accessControl.read.user_ids = accessControl.read.user_ids?.filter(
					(id) => id !== userId
				);
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
		<div class="text-sm font-semibold mb-1">{$i18n.t('Visibility')}</div>

		<div class="flex gap-2.5 items-center mb-1">
			<div>
				<div class="p-2 bg-black/5 dark:bg-white/5 rounded-full">
					{#if !isPublic}
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
					{:else}
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
								d="M6.115 5.19l.319 1.913A6 6 0 008.11 10.36L9.75 12l-.387.775c-.217.433-.132.956.21 1.298l1.348 1.348c.21.21.329.497.329.795v1.089c0 .426.24.815.622 1.006l.153.076c.433.217.956.132 1.298-.21l.723-.723a8.7 8.7 0 002.288-4.042 1.087 1.087 0 00-.358-1.099l-1.33-1.108c-.251-.21-.582-.299-.905-.245l-1.17.195a1.125 1.125 0 01-.98-.314l-.295-.295a1.125 1.125 0 010-1.591l.13-.132a1.125 1.125 0 011.3-.21l.603.302a.809.809 0 001.086-1.086L14.25 7.5l1.256-.837a4.5 4.5 0 001.528-1.732l.146-.292M6.115 5.19A9 9 0 1017.18 4.64M6.115 5.19A8.965 8.965 0 0112 3c1.929 0 3.716.607 5.18 1.64"
							/>
						</svg>
					{/if}
				</div>
			</div>

			<div>
				<select
					id="models"
					class="outline-hidden bg-transparent text-sm font-medium rounded-lg block w-fit pr-10 max-w-full placeholder-gray-400"
					value={isPublic ? 'public' : 'private'}
					on:change={(e) => {
						if (e.target && e.target.value === 'public') {
							isPublic = true;
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
							// 변경사항 저장
							onChange(accessControl);
						} else {
							isPublic = false;
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
							// 변경사항 저장
							onChange(accessControl);
						}
					}}
				>
					<option class="text-gray-700" value="private" selected>Private</option>
					<option class="text-gray-700" value="public" selected>Public</option>
				</select>

				<div class="text-xs text-gray-400 font-medium">
					{#if !isPublic}
						{$i18n.t('Only select users and groups with permission can access')}
					{:else}
						{$i18n.t('Accessible to all users')}
					{/if}
				</div>
			</div>
		</div>
	</div>
	{#if !isPublic}
		<!-- 그룹 권한 관리 섹션 -->
		{@const accessGroups = groups.filter((group) =>
			accessControl.write?.group_ids?.includes(group.id)
		)}
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
									{selectedGroupId ? '' : 'text-gray-500'}
									dark:placeholder-gray-500"
									bind:value={selectedGroupId}
								>
									<option class="text-gray-700" value="" disabled selected
										>{$i18n.t('Select a group')}</option
									>
									{#each groups.filter((group) => !accessControl.write?.group_ids?.includes(group.id)) as group}
										<option class="text-gray-700" value={group.id}>{group.name}</option>
									{/each}
								</select>
							</div>
						</div>
					</div>
				</div>

				<hr class="border-gray-100 dark:border-gray-700/10 mt-1.5 mb-2.5 w-full" />

				<div class="flex flex-col gap-2 mb-1 px-0.5">
					{#if accessGroups.length > 0}
						{#each accessGroups as group}
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
										class=""
										type="button"
										on:click={() => {
											if (accessRoles.includes('write') && accessControl) {
												if (accessControl.write?.group_ids?.includes(group.id)) {
													accessControl.write.group_ids = accessControl.write.group_ids?.filter(
														(group_id) => group_id !== group.id
													);
												} else {
													accessControl.write.group_ids = [
														...(accessControl.write?.group_ids || []),
														group.id
													];
												}
												// 강제로 UI 업데이트 트리거
												accessControl = { ...accessControl };
												// 변경사항 저장
												onChange(accessControl);
											}
										}}
									>
										{#if accessControl.write?.group_ids?.includes(group.id)}
											<Badge type={'success'} content={$i18n.t('Write')} />
										{:else}
											<Badge type={'info'} content={$i18n.t('Read')} />
										{/if}
									</button>

									<button
										class="rounded-full p-1 hover:bg-gray-100 dark:hover:bg-gray-850 transition"
										type="button"
										on:click={() => {
											if (accessControl) {
												// write 권한에서 제거
												if (accessControl.write) {
													accessControl.write.group_ids = accessControl.write.group_ids?.filter(
														(id) => id !== group.id
													);
												}
												
												// read 권한에서도 제거
												if (accessControl.read) {
													accessControl.read.group_ids = accessControl.read.group_ids?.filter(
														(id) => id !== group.id
													);
												}
												
												// 강제로 UI 업데이트 트리거
												accessControl = { ...accessControl };
												// 변경사항 저장
												onChange(accessControl);
											}
										}}
									>
										<XMark />
									</button>
								</div>
							</div>
						{/each}
					{:else}
						<div class="flex items-center justify-center">
							<div class="text-gray-500 text-xs text-center py-2 px-10">
								{$i18n.t('No groups with access, add a group to grant access')}
							</div>
						</div>
					{/if}
				</div>
			</div>
		</div>
		
		<!-- 사용자 권한 관리 섹션 -->
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
								{selectedUserId ? '' : 'text-gray-500'}
								dark:placeholder-gray-500"
								bind:value={selectedUserId}
							>
								<option class="text-gray-700" value="" disabled selected
									>{$i18n.t('Select a user')}</option
								>
								{#each filterAvailableUsers(users, accessControl?.write?.user_ids || []) as user}
									<option class="text-gray-700" value={user.id}>{user.name}</option>
								{/each}
							</select>
						</div>
					</div>
				</div>
			</div>
			
			<hr class="border-gray-100 dark:border-gray-700/10 mt-1.5 mb-2.5 w-full" />
			
			<div class="flex flex-col gap-2 mb-1 px-0.5">
				{#if accessControl && accessControl.write}
					{#each users.filter(user => accessControl.write?.user_ids?.includes(user.id)) as user}
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
										class=""
										type="button"
										on:click={() => {
											if (accessControl.write?.user_ids?.includes(user.id)) {
												accessControl.write.user_ids = accessControl.write.user_ids?.filter(
													(userId) => userId !== user.id
												);
											} else {
												accessControl.write.user_ids = [
													...(accessControl.write?.user_ids || []),
													user.id
												];
											}
											// 강제로 UI 업데이트 트리거
											accessControl = { ...accessControl };
											// 변경사항 저장
											onChange(accessControl);
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
									class="rounded-full p-1 hover:bg-gray-100 dark:hover:bg-gray-850 transition"
									type="button"
									on:click={() => onRemoveUser(user.id)}
								>
									<XMark />
								</button>
							</div>
						</div>
					{:else}
						<div class="flex items-center justify-center">
							<div class="text-gray-500 text-xs text-center py-2 px-10">
								{$i18n.t('No users with access, add a user to grant access')}
							</div>
						</div>
					{/each}
				{:else}
					<div class="flex items-center justify-center">
						<div class="text-gray-500 text-xs text-center py-2 px-10">
							{$i18n.t('No users with access, add a user to grant access')}
						</div>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
