<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	const i18n = getContext('i18n');

	import XMark from '$lib/components/icons/XMark.svelte';
	import Badge from '$lib/components/common/Badge.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { findUserById, findUserByEmail as apiFindUserByEmail } from '../apis/company';

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

	type UserInfo = {
		id: string;
		email: string;
		name?: string;
	};

	export let onChange: Function = () => {};
	export let accessRoles: string[] = ['read'];
	export let accessControl: AccessControlConfig | null = null;

	let userEmail: string = '';
	let users: UserInfo[] = [];
	let isLoading = false;

	onMount(() => {
		// Initialize access control if it's null
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
			// Make sure the structure is correct
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

		// Fetch user info for existing user_ids
		loadUsersInfo();
	});

	// Load user information for existing IDs
	async function loadUsersInfo() {
		if (!accessControl?.read?.user_ids?.length) return;
		
		try {
			const updatedUsers = [];
			
			for (const userId of accessControl.read.user_ids) {
				try {
					const result = await findUserById(userId);
					
					if (result.success && result.data) {
						updatedUsers.push({
							id: userId,
							email: result.data.email || userId,
							name: result.data.name || result.data.email || userId
						});
					} else {
						updatedUsers.push({ id: userId, email: userId });
					}
				} catch (error) {
					console.error(`Error fetching user with ID ${userId}:`, error);
					updatedUsers.push({ id: userId, email: userId });
				}
			}
			
			if (updatedUsers.length > 0) {
				users = updatedUsers;
			}
			
		} catch (error) {
			console.error('Failed to load user information:', error);
		}
	}

	// 액세스 컨트롤이 변경될 때 실행할 함수
	function handleAccessControlChange() {
		onChange(accessControl);
	}

	async function findUserByEmail(email: string): Promise<UserInfo | null> {
		try {
			isLoading = true;
			
			const result = await apiFindUserByEmail(email);
			if (result.success && result.data) {
				return { 
					id: result.data.id, 
					email: result.data.email,
					name: result.data.name || result.data.email
				};
			} else {
				toast.error(result.error || '해당 이메일의 사용자를 찾을 수 없습니다');
				return null;
			}
		} catch (error) {
			console.error('Error finding user:', error);
			toast.error('사용자 검색 중 오류가 발생했습니다');
			return null;
		} finally {
			isLoading = false;
		}
	}

	async function addUserEmail() {
		if (!userEmail.trim() || !isValidEmail(userEmail)) {
			toast.error('유효한 이메일 주소를 입력하세요');
			return;
		}

		if (users.some(user => user.email === userEmail)) {
			toast.error('이미 추가된 사용자입니다');
			userEmail = '';
			return;
		}

		const user = await findUserByEmail(userEmail);
		
		if (!user) {
			return;
		}
		
		if (accessControl && accessControl.read && accessControl.write) {
			if (!accessControl.read.user_ids.includes(user.id)) {
				accessControl.read.user_ids = [...accessControl.read.user_ids, user.id];
			}

			if (!accessControl.write.user_ids.includes(user.id)) {
				accessControl.write.user_ids = [...accessControl.write.user_ids, user.id];
			}

			users = [...users, user];
			
			userEmail = '';
			
			// 사용자를 추가한 후 onChange 호출
			handleAccessControlChange();
		}
	}

	function removeUser(userToRemove: UserInfo) {
		if (accessControl && accessControl.read && accessControl.write) {
			accessControl.read.user_ids = accessControl.read.user_ids.filter(id => id !== userToRemove.id);
			accessControl.write.user_ids = accessControl.write.user_ids.filter(id => id !== userToRemove.id);
			
			users = users.filter(user => user.id !== userToRemove.id);
			
			// 사용자를 제거한 후 onChange 호출
			handleAccessControlChange();
		}
	}

	function isValidEmail(email: string): boolean {
		const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
		return emailRegex.test(email);
	}
</script>

<div class="rounded-lg flex flex-col gap-2">
	<div class="mb-2">
		<div class="flex flex-row gap-2 w-full items-center">
			<input
				type="email"
				placeholder="이메일 주소를 추가하여 공유"
				bind:value={userEmail}
				class="outline-hidden bg-transparent text-sm rounded-lg block flex-1 px-3 py-2 border border-gray-200 dark:border-gray-700"
				on:keydown={(e) => {
					if (e.key === 'Enter') {
						addUserEmail();
					}
				}}
				disabled={isLoading}
			/>
			<button
				class="px-3 py-2 bg-transparent text-blue-500 border border-blue-500 rounded-lg text-sm whitespace-nowrap"
				on:click={addUserEmail}
				disabled={isLoading}
			>
				{#if isLoading}
					<span class="inline-block w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-1"></span>
				{/if}
				{$i18n.t('추가')}
			</button>
		</div>
	</div>

	<div>

		<hr class="border-gray-100 dark:border-gray-700/10 mt-1.5 mb-2.5 w-full" />

		<div class="flex flex-col gap-2 mb-1 px-0.5">
			{#if users.length > 0}
				{#each users as user}
					<div class="flex items-center gap-3 justify-between text-xs w-full transition">
						<div class="flex items-center gap-1.5 flex-1 min-w-0 font-medium">
							<div class="flex-shrink-0">
								<svg xmlns="http://www.w3.org/2000/svg" class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
									<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
									<circle cx="12" cy="7" r="4" />
								</svg>
							</div>
							<div class="truncate">
								{user.name} ({user.email})
							</div>
						</div>

						<div class="flex-shrink-0 flex justify-end items-center gap-0.5">
							<Badge type={'success'} content={$i18n.t('읽기/쓰기')} />
							
							<button
								class="rounded-full p-1 hover:bg-gray-100 dark:hover:bg-gray-850 transition"
								type="button"
								on:click={() => removeUser(user)}
							>
								<XMark />
							</button>
						</div>
					</div>
				{/each}
			{:else}
				<div class="flex items-center justify-center">
					<div class="text-gray-500 text-xs text-center py-2 px-10">
						{$i18n.t('접근 권한이 있는 사용자가 없습니다')}
					</div>
				</div>
			{/if}
		</div>
	</div>
</div> 