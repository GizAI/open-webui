<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';

	import { user, config, settings } from '$lib/stores';
	import { updateUserProfile, createAPIKey, getAPIKey, getSessionUser } from '$lib/apis/auths';

	import UpdatePassword from './Account/UpdatePassword.svelte';
	import { getGravatarUrl } from '$lib/apis/utils';
	import { generateInitialsImage, canvasPixelTest } from '$lib/utils';
	import { copyToClipboard } from '$lib/utils';
	import Plus from '$lib/components/icons/Plus.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';

	const i18n = getContext('i18n');

	export let saveHandler: Function;
	export let saveSettings: Function;

	let profileImageUrl = '';
	let name = '';

	let webhookUrl = '';
	let showAPIKeys = false;

	let JWTTokenCopied = false;

	let APIKey = '';
	let APIKeyCopied = false;
	let profileImageInputElement: HTMLInputElement;

	let referrerLinkCopied = false;

	const submitHandler = async () => {
		if (name !== $user?.name) {
			if (profileImageUrl === generateInitialsImage($user?.name) || profileImageUrl === '') {
				profileImageUrl = generateInitialsImage(name);
			}
		}

		if (webhookUrl !== $settings?.notifications?.webhook_url) {
			saveSettings({
				notifications: {
					...$settings.notifications,
					webhook_url: webhookUrl
				}
			});
		}

		const updatedUser = await updateUserProfile(localStorage.token, name, profileImageUrl).catch(
			(error) => {
				toast.error(`${error}`);
			}
		);

		if (updatedUser) {
			// Get Session User Info
			const sessionUser = await getSessionUser(localStorage.token).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			await user.set(sessionUser);
			return true;
		}
		return false;
	};

	const createAPIKeyHandler = async () => {
		APIKey = await createAPIKey(localStorage.token);
		if (APIKey) {
			toast.success($i18n.t('API Key created.'));
		} else {
			toast.error($i18n.t('Failed to create API Key.'));
		}
	};

	onMount(async () => {
		name = $user?.name;
		profileImageUrl = $user?.profile_image_url;
		webhookUrl = $settings?.notifications?.webhook_url ?? '';

		APIKey = await getAPIKey(localStorage.token).catch((error) => {
			console.log(error);
			return '';
		});
	});
</script>

<div class="flex flex-col h-full justify-between text-sm">
	<div class=" space-y-3 overflow-y-scroll max-h-[28rem] lg:max-h-full">
		<input
			id="profile-image-input"
			bind:this={profileImageInputElement}
			type="file"
			hidden
			accept="image/*"
			on:change={(e) => {
				const files = profileImageInputElement.files ?? [];
				let reader = new FileReader();
				reader.onload = (event) => {
					let originalImageUrl = `${event.target.result}`;

					const img = new Image();
					img.src = originalImageUrl;

					img.onload = function () {
						const canvas = document.createElement('canvas');
						const ctx = canvas.getContext('2d');

						// Calculate the aspect ratio of the image
						const aspectRatio = img.width / img.height;

						// Calculate the new width and height to fit within 250x250
						let newWidth, newHeight;
						if (aspectRatio > 1) {
							newWidth = 250 * aspectRatio;
							newHeight = 250;
						} else {
							newWidth = 250;
							newHeight = 250 / aspectRatio;
						}

						// Set the canvas size
						canvas.width = 250;
						canvas.height = 250;

						// Calculate the position to center the image
						const offsetX = (250 - newWidth) / 2;
						const offsetY = (250 - newHeight) / 2;

						// Draw the image on the canvas
						ctx.drawImage(img, offsetX, offsetY, newWidth, newHeight);

						// Get the base64 representation of the compressed image
						const compressedSrc = canvas.toDataURL('image/jpeg');

						// Display the compressed image
						profileImageUrl = compressedSrc;

						profileImageInputElement.files = null;
					};
				};

				if (
					files.length > 0 &&
					['image/gif', 'image/webp', 'image/jpeg', 'image/png'].includes(files[0]['type'])
				) {
					reader.readAsDataURL(files[0]);
				}
			}}
		/>

		<div class="space-y-1">
			<!-- <div class=" text-sm font-medium">{$i18n.t('Account')}</div> -->

			<div class="flex space-x-5">
				<div class="flex flex-col">
					<div class="self-center mt-2">
						<button
							class="relative rounded-full dark:bg-gray-700"
							type="button"
							on:click={() => {
								profileImageInputElement.click();
							}}
						>
							<img
								src={profileImageUrl !== '' ? profileImageUrl : generateInitialsImage(name)}
								alt="profile"
								class=" rounded-full size-16 object-cover"
							/>

							<div
								class="absolute flex justify-center rounded-full bottom-0 left-0 right-0 top-0 h-full w-full overflow-hidden bg-gray-700 bg-fixed opacity-0 transition duration-300 ease-in-out hover:opacity-50"
							>
								<div class="my-auto text-gray-100">
									<svg
										xmlns="http://www.w3.org/2000/svg"
										viewBox="0 0 20 20"
										fill="currentColor"
										class="w-5 h-5"
									>
										<path
											d="m2.695 14.762-1.262 3.155a.5.5 0 0 0 .65.65l3.155-1.262a4 4 0 0 0 1.343-.886L17.5 5.501a2.121 2.121 0 0 0-3-3L3.58 13.419a4 4 0 0 0-.885 1.343Z"
										/>
									</svg>
								</div>
							</div>
						</button>
					</div>
				</div>

				<div class="flex-1 flex flex-col self-center gap-0.5">
					<div class=" mb-0.5 text-sm font-medium">{$i18n.t('Profile Image')}</div>

					<div>
						<button
							class=" text-xs text-center text-gray-800 dark:text-gray-400 rounded-full px-4 py-0.5 bg-gray-100 dark:bg-gray-850"
							on:click={async () => {
								if (canvasPixelTest()) {
									profileImageUrl = generateInitialsImage(name);
								} else {
									toast.info(
										$i18n.t(
											'Fingerprint spoofing detected: Unable to use initials as avatar. Defaulting to default profile image.'
										),
										{
											duration: 1000 * 10
										}
									);
								}
							}}>{$i18n.t('Use Initials')}</button
						>

						<button
							class=" text-xs text-center text-gray-800 dark:text-gray-400 rounded-full px-4 py-0.5 bg-gray-100 dark:bg-gray-850"
							on:click={async () => {
								const url = await getGravatarUrl(localStorage.token, $user?.email);

								profileImageUrl = url;
							}}>{$i18n.t('Use Gravatar')}</button
						>

						<button
							class=" text-xs text-center text-gray-800 dark:text-gray-400 rounded-lg px-2 py-1"
							on:click={async () => {
								profileImageUrl = '/user.png';
							}}>{$i18n.t('Remove')}</button
						>
					</div>
				</div>
			</div>

			<div class="pt-0.5">
				<div class="flex flex-col w-full">
					<div class=" mb-1 text-xs font-medium">{$i18n.t('Name')}</div>

					<div class="flex-1">
						<input
							class="w-full text-sm dark:text-gray-300 dark:bg-gray-850 outline-hidden"
							type="text"
							bind:value={name}
							required
							placeholder={$i18n.t('Enter your name')}
						/>
					</div>
				</div>
			</div>

			{#if $config?.features?.enable_user_webhooks}
				<div class="pt-2">
					<div class="flex flex-col w-full">
						<div class=" mb-1 text-xs font-medium">{$i18n.t('Notification Webhook')}</div>

						<div class="flex-1">
							<input
								class="w-full rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-hidden"
								type="url"
								placeholder={$i18n.t('Enter your webhook URL')}
								bind:value={webhookUrl}
								required
							/>
						</div>
					</div>
				</div>
			{/if}
		</div>

		<div class="py-0.5">
			<UpdatePassword />
		</div>

		<hr class="border-gray-50 dark:border-gray-850 my-2" />

		<div class="flex justify-between items-center text-sm">
			<div class="font-medium">{$i18n.t('Referral Link')}</div>
		</div>
		<div class="flex flex-col gap-2">
			<div class="justify-between w-full">
				<div class="flex flex-col sm:flex-row mt-2">
					<input
						class="flex-1 rounded-lg py-2 px-4 text-sm dark:text-gray-300 dark:bg-gray-850 outline-hidden"
						type="text"
						value={`${window.location.origin}/auth?referrer_code=${$user.referral_code ?? ''}`}
						readonly
					/>

					<button
						class="mt-2 sm:mt-0 sm:ml-1.5 px-3 py-1.5 text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300 transition rounded-lg flex items-center justify-center border border-blue-200 dark:border-blue-800"
						on:click={() => {							
							copyToClipboard(`${window.location.origin}/auth?referrer_code=${$user.referral_code ?? ''}`);
							referrerLinkCopied = true;
							setTimeout(() => {
								referrerLinkCopied = false;
							}, 2000);
						}}
					>
						{#if referrerLinkCopied}
							<div class="flex items-center gap-1">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									viewBox="0 0 20 20"
									fill="currentColor"
									class="w-3.5 h-3.5"
								>
									<path
										fill-rule="evenodd"
										d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
										clip-rule="evenodd"
									/>
								</svg>
								<span class="text-xs">{$i18n.t('Copied!')}</span>
							</div>
						{:else}
							<div class="flex items-center gap-1">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									viewBox="0 0 16 16"
									fill="currentColor"
									class="w-3.5 h-3.5"
								>
									<path
										fill-rule="evenodd"
										d="M11.986 3H12a2 2 0 0 1 2 2v6a2 2 0 0 1-1.5 1.937V7A2.5 2.5 0 0 0 10 4.5H4.063A2 2 0 0 1 6 3h.014A2.25 2.25 0 0 1 8.25 1h1.5a2.25 2.25 0 0 1 2.236 2ZM10.5 4v-.75a.75.75 0 0 0-.75-.75h-1.5a.75.75 0 0 0-.75.75V4h3Z"
										clip-rule="evenodd"
									/>
									<path
										fill-rule="evenodd"
										d="M3 6a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h7a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1H3Zm1.75 2.5a.75.75 0 0 0 0 1.5h3.5a.75.75 0 0 0 0-1.5h-3.5ZM4 11.75a.75.75 0 0 1 .75-.75h3.5a.75.75 0 0 1 0 1.5h-3.5a.75.75 0 0 1-.75-.75Z"
										clip-rule="evenodd"
									/>
								</svg>
								<span class="text-xs">{$i18n.t('Copy Link')}</span>
							</div>
						{/if}
					</button>

					<button
						class="mt-2 sm:mt-0 sm:ml-1.5 px-3 py-1.5 text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300 transition rounded-lg flex items-center justify-center border border-blue-200 dark:border-blue-800"
						on:click={() => {
							if (navigator.share) {
								navigator.share({
									title: $i18n.t('Join with my referral link'),
									url: `${window.location.origin}/auth?referrer_code=${$user.referral_code ?? ''}`
								}).catch((error) => console.log('Error sharing:', error));
							} else {
								toast.info($i18n.t('Web Share API is not supported in your browser'));
							}
						}}
					>
						<div class="flex items-center gap-1">
							<svg 
								xmlns="http://www.w3.org/2000/svg" 
								viewBox="0 0 20 20" 
								fill="currentColor" 
								class="w-3.5 h-3.5"
							>
								<path 
									d="M13 4.5a2.5 2.5 0 1 1 .602 1.628l-6.5 3.25a2.5 2.5 0 0 1 0 1.244l6.5 3.25a2.5 2.5 0 1 1-.651.646l-6.5-3.25a2.5 2.5 0 1 1 0-2.536l6.5-3.25A2.5 2.5 0 0 1 13 4.5Z" 
								/>
							</svg>
							<span class="text-xs">{$i18n.t('Share')}</span>
						</div>
					</button>
				</div>
				<div class="text-xs text-gray-500 mt-1.5">
					{$i18n.t('Share this link to invite others to join.')}
				</div>
			</div>
		</div>

		
	</div>

	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
			on:click={async () => {
				const res = await submitHandler();

				if (res) {
					saveHandler();
				}
			}}
		>
			{$i18n.t('Save')}
		</button>
	</div>
</div>
