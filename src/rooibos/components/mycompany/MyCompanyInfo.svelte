<!-- CorpBookmarksBase.svelte -->
<script lang="ts">
	import Fuse from 'fuse.js';
	import { toast } from 'svelte-sonner';
	import { v4 as uuidv4 } from 'uuid';

	import { onMount, getContext, onDestroy, tick } from 'svelte';
	const i18n = getContext('i18n');

	import { page } from '$app/stores';
	import { showSidebar, knowledge as _knowledge, user, mobile } from '$lib/stores';

	import { updateFileDataContentById, uploadFile } from '$lib/apis/files';

	import { transcribeAudio } from '$lib/apis/audio';
	import { blobToFile } from '$lib/utils';

	import Spinner from '$lib/components/common/Spinner.svelte';
	import Files from './CorpBookmarksBase/Files.svelte';
	import AddFilesPlaceholder from '$lib/components/AddFilesPlaceholder.svelte';

	import AddContentMenu from './CorpBookmarksBase/AddContentMenu.svelte';
	import NoteEditorModal from '$rooibos/components/note/NoteEditorModal.svelte';

	import SyncConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import MenuLines from '$lib/components/icons/MenuLines.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { goto } from '$app/navigation';
	import ActionButtons from '../common/ActionButtons.svelte';
	import CompanyDetail from '../company/CompanyDetail.svelte';
	import { get } from 'svelte/store';
	import LockClosed from '$lib/components/icons/LockClosed.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import RooibosAccessControlModal from '../accesscontrol/RooibosAccessControlModal.svelte';
	import Messages from '$lib/components/chat/Messages.svelte';
	import { convertMessagesToHistory, createMessagesList } from '$lib/utils';
	import { getUserById } from '$lib/apis/users';

	type Bookmark = {
		id: string;
		company_id: string;
		company_name: string;
		roadAddress?: string;
		address?: string;
		category?: string[];
		business_registration_number?: number;
		industry?: string;
		representative?: string;
		birth_date?: string;
		establishment_date?: string;
		employee_count?: number;
		phone_number?: string;
		website?: string;
		distance_from_user?: number;
		created_at?: string;
		updated_at?: string;
		files: any[];
		master_id: string;
		latitude: string;
		longitude: string;
		bookmark_id?: string | null;
		bookmark_user_id?: string;
		fax_number?: string;
		email?: string;
		company_type?: string;
		founding_date?: string;
		industry_code1?: string;
		industry_code2?: string;
		main_product?: string;
		main_bank?: string;
		main_branch?: string;
		group_name?: string;
		stock_code?: string;
		corporate_number?: string;
		english_name?: string;
		trade_name?: string;
		fiscal_month?: string;
		region1?: string;
		region2?: string;
		industry_major?: string;
		industry_middle?: string;
		industry_small?: string;
		sme_type?: { sme_type: string; certificate_expiry_date: string }[];
		research_info?: {
			lab_name: string;
			lab_location: string;
			first_approval_date: string;
			research_field: string;
			division: string;
		}[];
		birth_year?: string;
		foundation_year?: string;
		is_family_shareholder?: string;
		access_control?: {
			read?: {
				group_ids: string[];
				user_ids: string[];
			};
			write?: {
				group_ids: string[];
				user_ids: string[];
			};
		} | null;
	};

	type FinancialData = {
		financial_company_id: string;
		year: string;
		revenue?: number;
		net_income?: number;
		operating_income?: number;
		total_assets?: number;
		total_liabilities?: number;
		total_equity?: number;
		capital_stock?: number;
		corporate_tax?: number;
		current_assets?: number;
		quick_assets?: number;
		inventory?: number;
		non_current_assets?: number;
		investment_assets?: number;
		tangible_assets?: number;
		intangible_assets?: number;
		current_liabilities?: number;
		non_current_liabilities?: number;
		retained_earnings?: number;
		profit?: number;
		sales_cost?: number;
		sales_profit?: number;
		sga?: number;
		other_income?: number;
		other_expenses?: number;
		pre_tax_income?: number;
	};

	let largeScreen = true;
	let pane: any;
	let showSidepanel = true;
	let minSize = 0;
	let bookmark: Bookmark | null = null;
	let financialData: FinancialData | null = null;
	let query = '';
	let showAddTextContentModal = false;
	let showSyncConfirmModal = false;
	let showAccessControlModal = false;
	let chatList: any = null;
	let inputFiles: any = null;
	let filteredItems: any = [];
	let selectedFile: any = null;
	let selectedFileId: any = null;
	let tempFileForNoteEditor: any = { id: 'temp-id' };
	let fuse: any = null;
	let debounceTimeout: any = null;
	let mediaQuery: any;
	let dragged = false;
	let id: any = null;
	let isShared = false;
	const currentUser = get(user);

	let previousModalState = false;
	let previousAccessControlModalState = false;
	
	let showChatModal = false;
	let sharedChat: any = null;
	let sharedChatHistory = {
		messages: {},
		currentId: null
	};
	let sharedChatMessages: any[] = [];
	let sharedChatTitle = '';
	let sharedChatAutoScroll = true;
	let sharedChatUser: any = null;
	let sharedChatSelectedModels = [''];
	
	function handleModalStateChange(currentModalState: boolean) {
		if (previousModalState && !currentModalState) {
			selectedFileId = null;
			selectedFile = null;
		}
		previousModalState = currentModalState;
	}
	
	function handleAccessControlModalStateChange(currentModalState: boolean) {
		previousAccessControlModalState = currentModalState;
	}
	
	$: handleModalStateChange(showAddTextContentModal);
	$: handleAccessControlModalStateChange(showAccessControlModal);

	$: if (bookmark && bookmark.files) {
		fuse = new Fuse(bookmark.files, {
			keys: ['meta.name', 'meta.description']
		});
	}

	$: if (fuse) {
		filteredItems = query
			? fuse.search(query).map((e: any) => {
					return e.item;
				})
			: (bookmark?.files ?? []);
	}

	$: if (selectedFileId) {
		const file = (bookmark?.files ?? []).find((file) => file.id === selectedFileId);
		if (file) {
			file.data = file.data ?? { content: '' };
			selectedFile = file;

			if (!showAddTextContentModal) {
				showAddTextContentModal = true;
			}
		} else {
			selectedFile = null;
		}
	} else {
		selectedFile = null;
	}

	const createFileFromText = (name: string, content: string) => {
		const blob = new Blob([content], { type: 'text/plain' });
		const file = blobToFile(blob, `${name}.txt`);

		console.log(file);
		return file;
	};

	const uploadFileHandler = async (file) => {
		if (!file) {
			return;
		}
		
		const tempItemId = uuidv4();
		const fileItem = {
			type: 'file',
			file: '',
			id: null,
			url: '',
			name: file.name,
			size: file.size,
			status: 'uploading',
			error: '',
			itemId: tempItemId
		};

		bookmark.files = [...(bookmark.files ?? []), fileItem];

		if (['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/x-m4a'].includes(file['type'])) {
			const res = await transcribeAudio(localStorage.token, file).catch((error) => {
				toast.error(error);
				return null;
			});

			if (res) {
				console.log(res);
				const blob = new Blob([res.text], { type: 'text/plain' });
				file = blobToFile(blob, `${file.name}.txt`);
			}
		}

		try {
			const uploadedFile = await uploadFile(localStorage.token, file);

			if (uploadedFile) {				
				await addFileHandler(uploadedFile.id);
				
				if (bookmark && bookmark.files) {
					bookmark.files = bookmark.files.map(f => {
						if (f.itemId === tempItemId || (f.name === file.name && f.status === 'uploading')) {
							return { ...f, status: 'completed', id: uploadedFile.id };
						}
						return f;
					});
				}
				return uploadedFile;
			} else {
				toast.error($i18n.t('Failed to upload file.'));
			}
		} catch (e) {
			toast.error($i18n.t('Failed to upload file.'));
		}
	};

	const uploadDirectoryHandler = async () => {
		const isFileSystemAccessSupported = 'showDirectoryPicker' in window;

		try {
			if (isFileSystemAccessSupported) {
				await handleModernBrowserUpload();
			} else {
				await handleFirefoxUpload();
			}
		} catch (error) {
			handleUploadError(error);
		}
	};

	const hasHiddenFolder = (path: any) => {
		return path.split('/').some((part: any) => part.startsWith('.'));
	};

	const handleModernBrowserUpload = async () => {
		const dirHandle = await window.showDirectoryPicker();
		let totalFiles = 0;
		let uploadedFiles = 0;

		const updateProgress = () => {
			const percentage = (uploadedFiles / totalFiles) * 100;
			toast.info(`Upload Progress: ${uploadedFiles}/${totalFiles} (${percentage.toFixed(2)}%)`);
		};

		async function countFiles(dirHandle: any) {
			for await (const entry of dirHandle.values()) {
				if (entry.name.startsWith('.')) continue;

				if (entry.kind === 'file') {
					totalFiles++;
				} else if (entry.kind === 'directory') {
					if (!entry.name.startsWith('.')) {
						await countFiles(entry);
					}
				}
			}
		}

		async function processDirectory(dirHandle: any, path = '') {
			for await (const entry of dirHandle.values()) {
				if (entry.name.startsWith('.')) continue;

				const entryPath = path ? `${path}/${entry.name}` : entry.name;

				if (hasHiddenFolder(entryPath)) continue;

				if (entry.kind === 'file') {
					const file = await entry.getFile();
					const fileWithPath = new File([file], entryPath, { type: file.type });

					await uploadFileHandler(fileWithPath);
					uploadedFiles++;
					updateProgress();
				} else if (entry.kind === 'directory') {
					if (!entry.name.startsWith('.')) {
						await processDirectory(entry, entryPath);
					}
				}
			}
		}

		await countFiles(dirHandle);
		updateProgress();

		if (totalFiles > 0) {
			await processDirectory(dirHandle);
		} else {
			console.log('No files to upload.');
		}
	};

	const handleFirefoxUpload = async () => {
		return new Promise((resolve, reject) => {
			const input = document.createElement('input');
			input.type = 'file';
			input.webkitdirectory = true;
			input.directory = true;
			input.multiple = true;
			input.style.display = 'none';

			document.body.appendChild(input);

			input.onchange = async () => {
				try {
					const files = Array.from(input.files).filter(
						(file) => !hasHiddenFolder(file.webkitRelativePath)
					);

					let totalFiles = files.length;
					let uploadedFiles = 0;

					const updateProgress = () => {
						const percentage = (uploadedFiles / totalFiles) * 100;
						toast.info(
							`Upload Progress: ${uploadedFiles}/${totalFiles} (${percentage.toFixed(2)}%)`
						);
					};

					updateProgress();

					for (const file of files) {
						if (!file.name.startsWith('.')) {
							const relativePath = file.webkitRelativePath || file.name;
							const fileWithPath = new File([file], relativePath, { type: file.type });

							await uploadFileHandler(fileWithPath);
							uploadedFiles++;
							updateProgress();
						}
					}

					document.body.removeChild(input);
					resolve();
				} catch (error) {
					reject(error);
				}
			};

			input.onerror = (error) => {
				document.body.removeChild(input);
				reject(error);
			};

			input.click();
		});
	};

	const handleUploadError = (error: any) => {
		if (error.name === 'AbortError') {
			toast.info('Directory selection was cancelled');
		} else {
			toast.error('Error accessing directory');
			console.error('Directory access error:', error);
		}
	};

	const syncDirectoryHandler = async () => {
		if ((bookmark?.files ?? []).length > 0) {
			const res = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/${id}/file/reset`, {
				method: 'POST',
				headers: {
					Accept: 'application/json',
					'Content-Type': 'application/json'
				}
			});

			if (res) {
				toast.success($i18n.t('Bookmark reset successfully.'));

				uploadDirectoryHandler();
			}
		} else {
			uploadDirectoryHandler();
		}
	};

	const addFileHandler = async (fileId: string) => {
		const res = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/${bookmark.bookmark_id}/file/add`, {
			method: 'POST',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				file_id: fileId
			})
		});

		if (res.ok) {
			const data = await res.json();
			if (bookmark && bookmark.files) {
				bookmark.files = bookmark.files.map(file => {
					if (file.id === fileId || file.status === 'uploading') {
						return { ...file, status: 'completed' };
					}
					return file;
				});
			}			
		} else {
			toast.error($i18n.t('Failed to add file.'));
		}
	};

	const deleteFileHandler = async (fileId: string) => {
		const res = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/${id}/file/remove`, {
			method: 'POST',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				file_id: fileId
			})
		});

		if (res.ok) {
			filteredItems = filteredItems.filter((item) => item.id !== fileId);
			toast.success($i18n.t('File removed successfully.'));
		}
	};

	const updateFileContentHandler = async () => {
		const fileId = selectedFile.id;
		const content = selectedFile.data.content;

		const res = await updateFileDataContentById(localStorage.token, fileId, content).catch((e) => {
			toast.error(e);
		});
	};

	const changeDebounceHandler = () => {
		if (debounceTimeout) {
			clearTimeout(debounceTimeout);
		}

		debounceTimeout = setTimeout(async () => {
			if (bookmark?.company_name.trim() === '' || bookmark.description.trim() === '') {
				toast.error($i18n.t('Please fill in all fields.'));
				return;
			}
		}, 1000);
	};

	const handleMediaQuery = async (e: any) => {
		if (e.matches) {
			largeScreen = true;
		} else {
			largeScreen = false;
		}
	};

	const onDragOver = (e: any) => {
		e.preventDefault();

		if (e.dataTransfer?.types?.includes('Files')) {
			dragged = true;
		} else {
			dragged = false;
		}
	};

	const onDragLeave = () => {
		dragged = false;
	};

	const onDrop = async (e: any) => {
		e.preventDefault();
		dragged = false;

		if (e.dataTransfer?.types?.includes('Files')) {
			if (e.dataTransfer?.files) {
				const inputFiles = e.dataTransfer?.files;

				if (inputFiles && inputFiles.length > 0) {
					for (const file of inputFiles) {
						await uploadFileHandler(file);
					}
				} else {
					toast.error($i18n.t(`File not found.`));
				}
			}
		}
	};

	onMount(async () => {
		const urlParams = new URLSearchParams(window.location.search);
		isShared = urlParams.get('shared') === 'true';

		mediaQuery = window.matchMedia('(min-width: 1024px)');

		mediaQuery.addEventListener('change', handleMediaQuery);
		handleMediaQuery(mediaQuery);

		const container = document.getElementById('collection-container');

		minSize = !largeScreen ? 100 : Math.floor((300 / container.clientWidth) * 100);

		const resizeObserver = new ResizeObserver((entries) => {
			for (let entry of entries) {
				const width = entry.contentRect.width;
				const percentage = (300 / width) * 100;

				minSize = !largeScreen ? 100 : Math.floor(percentage);

				if (showSidepanel) {
					if (pane && pane.isExpanded() && pane.getSize() < minSize) {
						pane.resize(minSize);
					}
				}
			}
		});

		resizeObserver.observe(container);

		if (pane) {
			pane.expand();
		}

		id = $page.params.id;

		const queryParams = new URLSearchParams({
			business_registration_number:
				bookmark?.business_registration_number !== undefined
					? bookmark?.business_registration_number.toString()
					: '',
			user_id: currentUser?.id ?? '',
			is_shared: isShared.toString()
		});

		const response = await fetch(
			`${WEBUI_API_BASE_URL}/rooibos/mycompanies/${id}?${queryParams.toString()}`,
			{
				method: 'GET',
				headers: {
					Accept: 'application/json',
					'Content-Type': 'application/json',
					authorization: `Bearer ${localStorage.token}`
				}
			}
		);

		const data = await response.json();
		
		if(data.success === false) {
			await goto('/');
			return;
		}
		
		bookmark = data.bookmark[0];
		chatList = data.chatList;
		

		filteredItems = bookmark?.files ?? [];

		const dropZone = document.querySelector('body');
		dropZone?.addEventListener('dragover', onDragOver);
		dropZone?.addEventListener('drop', onDrop);
		dropZone?.addEventListener('dragleave', onDragLeave);

		// 북마크 정보가 로드된 후 isShared 상태를 업데이트하는 리액티브 선언
		$: if (bookmark && currentUser) {
			// 북마크 소유자가 현재 사용자와 다른 경우 공유된 기업으로 처리
			isShared = isShared || (bookmark.bookmark_user_id !== currentUser.id);
		}
	});

	onDestroy(() => {
		mediaQuery?.removeEventListener('change', handleMediaQuery);
		const dropZone = document.querySelector('body');
		dropZone?.removeEventListener('dragover', onDragOver);
		dropZone?.removeEventListener('drop', onDrop);
		dropZone?.removeEventListener('dragleave', onDragLeave);
	});

	export let isFullscreen = false;

	function closeCompanyInfo() {
		isFullscreen = false;
	}

	// 채팅 공유 ID 생성 함수
	async function createShareId(chatId: string) {
		try {
			const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/${chatId}/share`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					Authorization: `Bearer ${localStorage.token}`
				}
			});
			
			if (!response.ok) {
				throw new Error('Failed to create share ID');
			}
			
			const data = await response.json();
			return data.share_id;
		} catch (error) {
			console.error('Error creating share ID:', error);
			toast.error('채팅 공유 ID 생성에 실패했습니다.');
			return null;
		}
	}

	async function moveToExistingChat(chat: any) {
		try {
			if (!chat || !chat.id) {
				console.error('Invalid chat data');
				return;
			}
			
			const isOwner = currentUser && bookmark && currentUser.id === bookmark.bookmark_user_id;
			
			if (isOwner) {
				goto(`/c/${chat.id}`);
				return;
			}
			
			let shareId = chat.share_id;
			
			if (!shareId) {
				shareId = await createShareId(chat.id);
				if (!shareId) {
					goto(`/c/${chat.id}`);
					return;
				}
			}
			
			// 공유된 채팅 데이터 가져오기
			const response = await fetch(
				`${WEBUI_API_BASE_URL}/rooibos/mycompanies/s/${shareId}`,
				{
					method: 'GET',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: `Bearer ${localStorage.token}`
					}
				}
			);

			const data = await response.json();
			
			if (data.success) {
				sharedChat = data.data;
				
				sharedChatUser = await getUserById(localStorage.token, sharedChat.user_id).catch((error) => {
					console.error(error);
					return null;
				});

				const chatContent = sharedChat.chat;

				if (chatContent) {
					sharedChatSelectedModels =
						(chatContent?.models ?? undefined) !== undefined
							? chatContent.models
							: [chatContent.models ?? ''];
					
					sharedChatHistory =
						(chatContent?.history ?? undefined) !== undefined
							? chatContent.history
							: convertMessagesToHistory(chatContent.messages);
					
					sharedChatTitle = chatContent.title;
					sharedChatAutoScroll = true;
					
					await tick();
					
					if (sharedChatMessages.length > 0) {
						sharedChatHistory.messages[sharedChatMessages.at(-1).id].done = true;
					}
					
					await tick();
					
					// 모달 표시
					showChatModal = true;
				}
			} else {
				console.error("채팅을 로드하는 데 실패했습니다:", data.message);
				toast.error("채팅을 로드하는 데 실패했습니다");
			}
		} catch (error) {
			console.error('Error in moveToExistingChat:', error);
			toast.error("채팅을 로드하는 데 실패했습니다");
		}
	}

	// 메시지 목록 업데이트를 위한 반응형 선언
	$: sharedChatMessages = sharedChatHistory && sharedChatHistory.currentId 
			? createMessagesList(sharedChatHistory, sharedChatHistory.currentId) 
			: [];

	async function handleAccessControlChange(newAccessControl) {
		if (!bookmark || !bookmark.bookmark_id) return;
		
		try {			
			const response = await fetch(
				`${WEBUI_API_BASE_URL}/rooibos/mycompanies/${bookmark.bookmark_id}/accessControl`,
				{
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						Authorization: `Bearer ${localStorage.token}`
					},
					body: JSON.stringify({ access_control: newAccessControl })
				}
			);
			
			const result = await response.json();
			
			if (response.ok) {
				const updatedAccessControl = result.data.access_control;
				
				const updatedBookmark = { ...bookmark };
				
				if (newAccessControl === null) {
					updatedBookmark.access_control = null;
				} else {
					// Keep the user_ids that were set in the UI
					updatedBookmark.access_control = updatedAccessControl;
					
					// If for some reason the server response doesn't include the user_ids,
					// use the ones from the UI input
					if (updatedBookmark.access_control && 
						newAccessControl && 
						newAccessControl.read && 
						newAccessControl.read.user_ids) {
						
						if (!updatedBookmark.access_control.read) {
							updatedBookmark.access_control.read = {
								group_ids: [],
								user_ids: []
							};
						}
						
						updatedBookmark.access_control.read.user_ids = newAccessControl.read.user_ids;
					}
					
					if (updatedBookmark.access_control && 
						newAccessControl && 
						newAccessControl.write && 
						newAccessControl.write.user_ids) {
						
						if (!updatedBookmark.access_control.write) {
							updatedBookmark.access_control.write = {
								group_ids: [],
								user_ids: []
							};
						}
						
						updatedBookmark.access_control.write.user_ids = newAccessControl.write.user_ids;
					}
				}
				
				bookmark = updatedBookmark;
				
			} else {
				console.error(result.message);
			}
		} catch (error) {
			toast.error($i18n.t('Failed to update access control'));
			console.error(error);
		}
	}
</script>

{#if dragged}
	<div
		class="fixed {$showSidebar
			? 'left-0 md:left-[260px] md:w-[calc(100%-260px)]'
			: 'left-0'}  w-full h-full flex z-50 touch-none pointer-events-none"
		id="dropzone"
		role="region"
		aria-label="Drag and Drop Container"
	>
		<div class="absolute w-full h-full backdrop-blur bg-gray-800/40 flex justify-center">
			<div class="m-auto pt-64 flex flex-col justify-center">
				<div class="max-w-md">
					<AddFilesPlaceholder>
						<div class=" mt-2 text-center text-sm dark:text-gray-200 w-full">
							Drop any files here to add to my documents
						</div>
					</AddFilesPlaceholder>
				</div>
			</div>
		</div>
	</div>
{/if}

<SyncConfirmDialog
	bind:show={showSyncConfirmModal}
	message={$i18n.t(
		'This will reset the bookmark base and sync all files. Do you wish to continue?'
	)}
	on:confirm={() => {
		syncDirectoryHandler();
	}}
/>

<NoteEditorModal
	bind:show={showAddTextContentModal}
	initialTitle={selectedFile ? selectedFile?.meta?.name || '' : ''}
	initialContent={selectedFile ? selectedFile?.data?.content || '' : ''}
	selectedFile={selectedFile || tempFileForNoteEditor}
	on:autosave={(e) => {
		if (selectedFile) {
			selectedFile.data.content = e.detail.content;
			updateFileContentHandler();
		}
	}}
	on:submit={(e) => {		
		if (selectedFile) {
			selectedFile.data.content = e.detail.content;
			updateFileContentHandler();
		} else {
			const file = createFileFromText(e.detail.name, e.detail.content);
			uploadFileHandler(file);
		}
		showAddTextContentModal = false;
		selectedFileId = null;
	}}
	on:uploadRequest={async (e) => {
		const file = createFileFromText(e.detail.name, e.detail.content);
		if (file) {
		  const uploadedFile = await uploadFileHandler(file);
		  if (uploadedFile && e.detail.callback) {
			e.detail.callback(uploadedFile);
		  }
		  selectedFile = uploadedFile;
		}
		showAddTextContentModal = true;
	}}
/>

<input
	id="files-input"
	bind:files={inputFiles}
	type="file"
	multiple
	hidden
	on:change={async () => {
		if (inputFiles && inputFiles.length > 0) {
			for (const file of inputFiles) {
				await uploadFileHandler(file);
			}

			inputFiles = null;
			const fileInputElement = document.getElementById('files-input');

			if (fileInputElement) {
				fileInputElement.value = '';
			}
		} else {
			toast.error($i18n.t(`File not found.`));
		}
	}}
/>
{#if bookmark}
	<div
		class="sticky border-b border-gray-200 top-0 z-10 shrink-0 px-4 pt-2 pb-1 bg-white dark:bg-gray-900"
	>
		<div class="flex items-center justify-between w-full mb-1">
			<div class="flex items-center min-w-0 max-w-[60%]">
				{#if !$showSidebar}
					<button
						id="sidebar-toggle-button"
						class="cursor-pointer p-1.5 mr-2 flex rounded-xl hover:bg-gray-100 dark:hover:bg-gray-850 transition flex-shrink-0"
						on:click={() => {
							showSidebar.set(!$showSidebar);
						}}
						aria-label="Toggle Sidebar"
					>
						<div class="m-auto self-center">
							<MenuLines />
						</div>
					</button>
				{/if}
				<h1 class="{$mobile ? 'text-base sm:text-xl' : 'text-xl'} font-semibold mb-1 truncate">
					{bookmark.company_name}
				</h1>
			</div>

			<div class="flex items-center space-x-1 overflow-x-auto flex-shrink-0">
				{#if currentUser.id == bookmark.bookmark_user_id && bookmark}
					<div class="self-center flex-shrink-0">
						<button
							class="bg-gray-50 hover:bg-gray-100 text-black dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-white transition px-2 py-1 rounded-full flex gap-1 items-center"
							type="button"
							on:click={() => {
								showAccessControlModal = true;
							}}
						>
							<LockClosed strokeWidth="2.5" className="size-3.5" />

							<div class="text-sm font-medium flex-shrink-0">
								{$i18n.t('공유')}
							</div>
						</button>
					</div>
				{/if}
				<ActionButtons companyInfo={bookmark} financialData={financialData} {isShared} />
			</div>
		</div>
	</div>
{/if}

<div class="flex flex-col w-full translate-y-1" id="collection-container">
	{#if bookmark}
		<RooibosAccessControlModal 
			bind:show={showAccessControlModal}
			bind:accessControl={bookmark.access_control}
			onChange={(newAccessControl) => {
				handleAccessControlChange(newAccessControl);
			}}
			accessRoles={['read', 'write']}
		/>
		<div
			class="company-info-wrapper active {isFullscreen
				? 'fullscreen'
				: ''} flex flex-col w-full mt-4 h-[calc(100vh-8rem)]"
			class:mobile={$mobile}
		>
			<!-- attach file -->
			<div class="flex flex-row pb-2.5 gap-3">
				{#if largeScreen}
					<div class="flex-1 flex justify-start w-full h-full max-h-full">
						{#if selectedFile}
							<!-- 파일 내용은 이제 NoteEditorModal에서 표시됩니다 -->
							<div class="h-full flex w-full">
								<div class="m-auto text-xs text-center text-gray-200 dark:text-gray-700">
									{selectedFile?.meta?.name} 파일이 선택되었습니다. 편집기가 열립니다...
								</div>
							</div>
						{:else}
							<div class="h-full flex w-full">
								<div class="m-auto text-xs text-center text-gray-200 dark:text-gray-700">
									{$i18n.t('Drag and drop a file to upload or select a file to view')}
								</div>
							</div>
						{/if}
					</div>
				{:else if !largeScreen && selectedFileId !== null}
					<!-- 모바일에서도 NoteEditorModal을 사용합니다 -->
					<div class="h-full flex w-full">
						<div class="m-auto text-xs text-center text-gray-200 dark:text-gray-700">
							{selectedFile?.meta?.name} 파일이 선택되었습니다. 편집기가 열립니다...
						</div>
					</div>
				{/if}

				<div
					class="{largeScreen ? 'flex-shrink-0 w-72 max-w-72' : 'flex-1'}
					flex py-2 rounded-2xl border border-gray-50 h-full dark:border-gray-850"
				>
					<div class=" flex flex-col w-full space-x-2 rounded-lg h-full">
						<div class="w-full h-full flex flex-col">
							<div class=" px-3">
								<div class="flex mb-0.5">
									<div class=" self-center ml-1 mr-3">
										<svg
											xmlns="http://www.w3.org/2000/svg"
											viewBox="0 0 20 20"
											fill="currentColor"
											class="w-4 h-4"
										>
											<path
												fill-rule="evenodd"
												d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z"
												clip-rule="evenodd"
											/>
										</svg>
									</div>
									<input
										class=" w-full text-sm pr-4 py-1 rounded-r-xl outline-none bg-transparent"
										bind:value={query}
										placeholder={$i18n.t('첨부 파일')}
										on:focus={() => {
											selectedFileId = null;
										}}
									/>

									<div>
										<AddContentMenu
											on:upload={async(e) => {
												if (e.detail.type === 'directory') {
													uploadDirectoryHandler();
												} else if (e.detail.type === 'text') {
													selectedFileId = null;
													selectedFile = null;
													const file = await createFileFromText('새노트', '<p></p>');
													const uploadedFile = await uploadFileHandler(file);
													selectedFileId = uploadedFile.id;
													showAddTextContentModal = true;
												} else {
													document.getElementById('files-input').click();
												}
											}}
											on:sync={(e) => {
												showSyncConfirmModal = true;
											}}
										/>
									</div>
								</div>
							</div>

							{#if filteredItems.length > 0}
								<div class=" flex overflow-y-auto h-full w-full scrollbar-hidden text-xs">
									<Files
										small
										files={filteredItems}
										{selectedFileId}
										on:click={(e) => {
											selectedFileId = selectedFileId === e.detail ? null : e.detail;
										}}
										on:delete={(e) => {
											selectedFileId = null;
											deleteFileHandler(e.detail);
										}}
									/>
								</div>
							{:else}
								<div class="my-3 flex flex-col justify-center text-center text-gray-500 text-xs">
									<div>
										{$i18n.t('No content found')}
									</div>
								</div>
							{/if}
						</div>
					</div>
				</div>

				<!-- 채팅 리스트 추가 -->
				{#if chatList.length > 0}
					<div
						class="{largeScreen
							? 'flex-shrink-0 w-60 max-w-60 border-l border-gray-200 dark:border-gray-700'
							: 'w-1/2'} flex flex-col"
					>
						<div class="px-2 py-1 border-b border-gray-200 dark:border-gray-700">
							<h2 class="text-xs">채팅</h2>
						</div>
						<div class="flex-1 overflow-y-auto p-1 max-h-[100px]">
							{#each chatList as chat}
								<button
									type="button"
									on:click={() => moveToExistingChat(chat)}
									class="mb-1 w-full text-left rounded bg-gray-50 dark:bg-gray-800 p-1 cursor-pointer text-xs"
								>
									{chat.title}
								</button>
							{/each}
						</div>
					</div>
				{/if}
			</div>

			<div class="flex-1 px-4 pb-4">
				<CompanyDetail company={bookmark} bind:financialData />
			</div>
		</div>
	{:else}
		<Spinner />
	{/if}
</div>

<Modal size="xl" bind:show={showChatModal}>
	<div class="flex flex-col h-[80vh] dark:bg-gray-900 text-gray-700 dark:text-gray-100">
		<div class="flex justify-between items-center px-5 py-3 border-b border-gray-200 dark:border-gray-700">
			<div class="text-xl font-semibold line-clamp-1">
				{sharedChatTitle}
			</div>
			<button
				class="self-center"
				on:click={() => {
					showChatModal = false;
				}}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="w-5 h-5"
				>
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>
		<div class="flex-1 overflow-auto">
			{#if sharedChat}
				<Messages
					className="h-full flex pt-4 pb-8"
					user={sharedChatUser}
					chatId={sharedChat.id}
					readOnly={true}
					selectedModels={sharedChatSelectedModels}
					processing=""
					bind:history={sharedChatHistory}
					bind:messages={sharedChatMessages}
					bind:autoScroll={sharedChatAutoScroll}
					bottomPadding={false}
					sendPrompt={() => {}}
					continueResponse={() => {}}
					regenerateResponse={() => {}}
				/>
			{:else}
				<div class="h-full flex w-full">
					<div class="m-auto text-center">
						<div class="text-gray-500 mb-4">채팅 내용을 불러오는 중입니다...</div>
					</div>
				</div>
			{/if}
		</div>
	</div>
</Modal>
