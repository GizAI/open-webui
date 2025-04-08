<!-- CorpBookmarksBase.svelte -->
<script lang="ts">
	import Fuse from 'fuse.js';
	import { toast } from 'svelte-sonner';
	import { v4 as uuidv4 } from 'uuid';

	import { onMount, getContext, onDestroy, tick } from 'svelte';
	const i18n = getContext('i18n');

	import { page } from '$app/stores';
	import { showSidebar, knowledge as _knowledge, user, mobile } from '$lib/stores';

	import { updateFileDataContentById, uploadFile, updateFileFilenameById } from '$lib/apis/files';

	import { transcribeAudio } from '$lib/apis/audio';
	import { blobToFile } from '$lib/utils';

	import Spinner from '$lib/components/common/Spinner.svelte';
	import Files from './CorpBookmarksBase/Files.svelte';
	import AddFilesPlaceholder from '$lib/components/AddFilesPlaceholder.svelte';

	import AddContentMenu from './CorpBookmarksBase/AddContentMenu.svelte';
	import NoteEditor from '$rooibos/components/note/NoteEditor.svelte';

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
	import { formatDate } from '$rooibos/components/common/helper';
	import { formatFileSize } from '$lib/utils';
	import PrivateCompanyDetail from '$rooibos/components/company/PrivateCompanyDetail.svelte';

	
	export let isPrivateCompany = false;
	export let entityType = 'company'; // Default to 'company' if not specified
	
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
	let showSyncConfirmModal = false;
	let showAccessControlModal = false;
	let chatList: any = null;
	let inputFiles: any = null;
	let filteredItems: any = [];
	let memoItems: any = [];
	let selectedFile: any = null;
	let selectedFileId: any = null;
	let tempFileForNoteEditor: any = { id: 'temp-id' };
	let fuse: any = null;
	let memoFuse: any = null;
	let debounceTimeout: any = null;
	let mediaQuery: any;
	let dragged = false;
	let id: any = null;
	let isShared = false;
	const currentUser = get(user);

	// 사용자 정보를 캐시하기 위한 맵
	let userCache = new Map();
	
	// 사용자 정보를 가져오는 함수
	async function getUserInfo(userId: string) {
		if (userCache.has(userId)) {
			return userCache.get(userId);
		}
		
		try {
			const response = await fetch(`${WEBUI_API_BASE_URL}/users/${userId}`, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${localStorage.token}`
				}
			});
			
			if (!response.ok) {
				throw new Error('사용자 정보를 가져오는데 실패했습니다.');
			}
			
			const data = await response.json();
			userCache.set(userId, data);
			return data;
		} catch (error) {
			console.error('사용자 정보 조회 오류:', error);
			return { name: '알 수 없는 사용자' };
		}
	}

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
	
	// 섹션 표시 여부 상태
	let showMemosSection = true;
	let showFilesSection = true;
	let showChatsSection = true;
	
	// 검색 상태
	let memoQuery = '';
	let fileQuery = '';

	// 현재 표시할 콘텐츠 상태 추가
	let contentType = 'company'; // 'company', 'file', 'memo'
	let showFileCloseButton = false;
	
	$: if (selectedFileId && selectedFile) {
		// 메모 파일인 경우 모달로 열지 않고 콘텐츠 영역에 표시
		if (selectedFile.meta?.name?.toLowerCase().endsWith('.txt')) {
			contentType = 'memo';
		} else {
			contentType = 'file';
		}
		showFileCloseButton = true;
	} else if (!selectedFileId && !selectedFile) {
		contentType = 'company';
		showFileCloseButton = false;
	}

	// 모달 상태 변경 로직 수정
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

	// 필요한 모달에 reactive 설정
	$: handleAccessControlModalStateChange(showAccessControlModal);

	$: if (bookmark && bookmark.files) {
		// txt 파일과 기타 파일을 분리
		memoItems = bookmark.files.filter(file => 
			file.meta && file.meta.name && file.meta.name.toLowerCase().endsWith('.txt')
		);
		filteredItems = bookmark.files.filter(file => 
			!file.meta || !file.meta.name || !file.meta.name.toLowerCase().endsWith('.txt')
		);
		
		fuse = new Fuse(filteredItems, {
			keys: ['meta.name', 'meta.description']
		});
		
		memoFuse = new Fuse(memoItems, {
			keys: ['meta.name', 'meta.description']
		});
	}

	$: if (fuse) {
		filteredItems = fileQuery
			? fuse.search(fileQuery).map((e: any) => {
					return e.item;
				})
			: (bookmark?.files.filter(file => 
				!file.meta || !file.meta.name || !file.meta.name.toLowerCase().endsWith('.txt')
			) ?? []);
	}
	
	$: if (memoFuse) {
		memoItems = memoQuery
			? memoFuse.search(memoQuery).map((e: any) => {
					return e.item;
				})
			: (bookmark?.files.filter(file => 
				file.meta && file.meta.name && file.meta.name.toLowerCase().endsWith('.txt')
			) ?? []);
	}

	$: if (selectedFileId) {
		const file = (bookmark?.files ?? []).find((file) => file.id === selectedFileId);
		if (file) {
			file.data = file.data ?? { content: '' };
			selectedFile = file;

			// txt 파일인 경우 콘텐츠 영역에 표시
			const isTxtFile = file.meta?.name?.toLowerCase().endsWith('.txt');
			if (isTxtFile) {
				contentType = 'memo';
			} else {
				contentType = 'file';
			}
		} else {
			selectedFile = null;
			selectedFileId = null;
			contentType = 'company';
		}
	} else {
		selectedFile = null;
		if (!contentType) contentType = 'company';
	}

	const createFileFromText = (name: string, content: string) => {
		// 이름에서 모든 .txt 확장자 제거
		let cleanedName = name;
		while(cleanedName.toLowerCase().endsWith('.txt')) {
			cleanedName = cleanedName.substring(0, cleanedName.length - 4);
		}
		
		// 확장자 한 번만 추가
		const fileName = cleanedName + '.txt';
		const blob = new Blob([content], { type: 'text/plain' });
		const file = blobToFile(blob, fileName);

		console.log(file);
		return file;
	};

	// 메모 생성 및 업로드 함수
	const createAndUploadMemo = async (name, content) => {
		selectedFileId = null;
		selectedFile = null;
		
		// 이름에서 모든 .txt 확장자 제거
		let cleanedName = name;
		while(cleanedName.toLowerCase().endsWith('.txt')) {
			cleanedName = cleanedName.substring(0, cleanedName.length - 4);
		}
		
		// 확장자를 한 번만 추가하여 파일 생성
		const file = createFileFromText(cleanedName, content || '<p></p>');
		const tempItemId = uuidv4();

		// 임시 메모 항목 생성 (확장자 한 번만 추가)
		const tempMemoItem = {
			type: 'file',
			file: '',
			id: tempItemId,
			url: '',
			meta: { name: `${cleanedName}.txt` },
			size: file.size,
			status: 'uploading',
			error: '',
			itemId: tempItemId
		};

		// 임시 항목을 메모 리스트에 추가
		memoItems = [...memoItems, tempMemoItem];

		const uploadedFile = await uploadFileHandler(file);
		
		if (uploadedFile) {
			// 북마크 파일 목록에서 최신 상태 가져오기
			if (bookmark && bookmark.files) {
				// txt 파일과 기타 파일을 다시 분리해서 할당
				memoItems = bookmark.files.filter(file => 
					file.meta && file.meta.name && file.meta.name.toLowerCase().endsWith('.txt')
				).map(item => {
					// 임시 항목을 업로드된 파일로 대체
					if (item.itemId === tempItemId) {
						return {
							...item,
							id: uploadedFile.id,
							status: 'completed'
						};
					}
					return item;
				});
				
				// 첨부파일 목록도 다시 필터링 (txt가 아닌 파일만)
				filteredItems = bookmark.files.filter(file => 
					!file.meta || !file.meta.name || !file.meta.name.toLowerCase().endsWith('.txt')
				);
			}
			
			// Fuse 인스턴스 업데이트
			fuse = new Fuse(filteredItems, {
				keys: ['meta.name', 'meta.description']
			});
			
			memoFuse = new Fuse(memoItems, {
				keys: ['meta.name', 'meta.description']
			});
			
			// 업로드된 파일 열기 - 오른쪽 영역에 표시
			setTimeout(() => {
				selectedFileId = uploadedFile.id;
				contentType = 'memo';
			}, 100);
		}
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
			meta: { name: file.name },
			size: file.size,
			status: 'uploading',
			error: '',
			itemId: tempItemId
		};

		// 모든 파일 타입을 bookmark.files에 추가
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
					
					// 파일 업로드 후 각 배열 재구성
					const isTxtFile = file.name.toLowerCase().endsWith('.txt');
					
					// txt 파일과 기타 파일을 분리
					memoItems = bookmark.files.filter(file => 
						file.meta && file.meta.name && file.meta.name.toLowerCase().endsWith('.txt')
					);
					
					filteredItems = bookmark.files.filter(file => 
						!file.meta || !file.meta.name || !file.meta.name.toLowerCase().endsWith('.txt')
					);
					
					// Fuse 인스턴스 업데이트
					fuse = new Fuse(filteredItems, {
						keys: ['meta.name', 'meta.description']
					});
					
					memoFuse = new Fuse(memoItems, {
						keys: ['meta.name', 'meta.description']
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
		return new Promise<void>((resolve, reject) => {
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
		if (!bookmark || !bookmark.bookmark_id) {
			console.error('북마크 정보가 없습니다.');
			return;
		}
		
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
		// 즉시 UI 업데이트
		filteredItems = filteredItems.filter((item) => item.id !== fileId);
		memoItems = memoItems.filter((item) => item.id !== fileId);
		
		// 메인 파일 목록에서도 제거
		if (bookmark && bookmark.files) {
			bookmark.files = bookmark.files.filter(file => file.id !== fileId);
		}
		
		// Fuse 인스턴스 업데이트
		if (filteredItems.length > 0) {
			fuse = new Fuse(filteredItems, {
				keys: ['meta.name', 'meta.description']
			});
		}
		
		if (memoItems.length > 0) {
			memoFuse = new Fuse(memoItems, {
				keys: ['meta.name', 'meta.description']
			});
		}
		
		// API 호출
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
			toast.success($i18n.t('File removed successfully.'));
		} else {
			// 실패 시 UI 복원 (롤백)
			await fetchAndUpdateFiles();
			toast.error($i18n.t('Failed to remove file.'));
		}
	};

	// 파일 목록 새로고침 함수
	const fetchAndUpdateFiles = async () => {
		if (!bookmark || !bookmark.bookmark_id) return;
		
		try {
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
			
			if (data.success !== false) {
				bookmark.files = data.bookmark[0].files || [];
				
				// txt 파일과 기타 파일을 분리
				memoItems = bookmark.files.filter(file => 
					file.meta && file.meta.name && file.meta.name.toLowerCase().endsWith('.txt')
				);
				filteredItems = bookmark.files.filter(file => 
					!file.meta || !file.meta.name || !file.meta.name.toLowerCase().endsWith('.txt')
				);
				
				// Fuse 인스턴스 업데이트
				fuse = new Fuse(filteredItems, {
					keys: ['meta.name', 'meta.description']
				});
				
				memoFuse = new Fuse(memoItems, {
					keys: ['meta.name', 'meta.description']
				});
			}
		} catch (error) {
			console.error('파일 목록 새로고침 중 오류:', error);
		}
	};

	const updateFileContentHandler = async () => {
		const fileId = selectedFile.id;
		const content = selectedFile.data.content;
		const filename = selectedFile.meta?.name;

		try {
			// 컨텐츠 업데이트
			const contentRes = await updateFileDataContentById(localStorage.token, fileId, content);
			
			// 파일명 업데이트 (확장자 포함)
			if (filename) {
				console.log('파일명 업데이트:', filename);
				const filenameRes = await updateFileFilenameById(localStorage.token, fileId, filename);
			}
			
			// 메모 파일인 경우 콘텐츠 영역에 표시
			if (filename && filename.toLowerCase().endsWith('.txt')) {
				contentType = 'memo';
			}
			
			toast.success($i18n.t('Content updated successfully.'));
		} catch (e) {
				toast.error(e);
		}
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

		// 데이터 로드
		await loadCompanyData();

		const dropZone = document.querySelector('body');
		dropZone?.addEventListener('dragover', onDragOver);
		dropZone?.addEventListener('drop', onDrop);
		dropZone?.addEventListener('dragleave', onDragLeave);
	});

	// 데이터 로드 함수
	async function loadCompanyData() {
		if (!id) {
			id = $page.params.id;
		}
		if (!id) return;
		
		try {
			const currentUser = get(user);
			const queryParams = new URLSearchParams({
				user_id: currentUser?.id ?? '',
				is_shared: isShared.toString()
			});
			
			// isPrivateCompany에 따라 다른 엔드포인트 호출
			const endpoint = isPrivateCompany ? 'private/' : '';
			const url = `${WEBUI_API_BASE_URL}/rooibos/mycompanies/${endpoint}${id}?${queryParams.toString()}`;
			
			const response = await fetch(url, {
				method: 'GET',
				headers: {
					Accept: 'application/json',
					'Content-Type': 'application/json',
					authorization: `Bearer ${localStorage.token}`
				}
			});
			
			const data = await response.json();
			
			if (data.success === false) {
				await goto('/');
				return;
			}
			
			bookmark = data.bookmark[0];
			chatList = data.chatList;
			
			// 북마크 소유자가 현재 사용자와 다른 경우 공유된 기업으로 처리
			if (bookmark && currentUser) {
				isShared = isShared || (bookmark.bookmark_user_id !== currentUser.id);
			}
			
			if (bookmark && bookmark.files) {
				// txt 파일과 기타 파일을 분리
				memoItems = bookmark.files.filter((file) =>
					file.meta && file.meta.name && file.meta.name.toLowerCase().endsWith('.txt')
				);
				filteredItems = bookmark.files.filter((file) =>
					!file.meta || !file.meta.name || !file.meta.name.toLowerCase().endsWith('.txt')
				);
				
				fuse = new Fuse(filteredItems, {
					keys: ['meta.name', 'meta.description']
				});
				
				memoFuse = new Fuse(memoItems, {
					keys: ['meta.name', 'meta.description']
				});
			}
			
			if (!bookmark) {
				// 북마크가 없으면 페이지를 이동
				await goto('/');
				return;
			}
			
			// 모바일에서는 기본적으로 모든 섹션 접기
			if (!largeScreen) {
				showMemosSection = false;
				showFilesSection = false;
				showChatsSection = false;
			}
			// 메모 아이템이 없으면 메모 섹션 숨기기
			else if (memoItems.length === 0) {
				showMemosSection = false;
			}
			// 파일 아이템이 없으면 파일 섹션 숨기기
			else if (filteredItems.length === 0) {
				showFilesSection = false;
			}
			// 채팅 목록이 없으면 채팅 섹션 숨기기
			else if (!chatList || chatList.length === 0) {
				showChatsSection = false;
			}
		} catch (error) {
			console.error('회사 정보 로드 중 오류:', error);
			toast.error('데이터를 가져오는 중 오류가 발생했습니다.');
			await goto('/');
		}
	}

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

	const closeContent = () => {
		selectedFileId = null;
		selectedFile = null;
		contentType = 'company';
		showFileCloseButton = false;
	};

	const updateFileContent = async (file, newContent) => {
		if (!file || !file.id) return;
		
		try {
			const response = await updateFileDataContentById(localStorage.token, file.id, newContent);
			
			if (response && response.status === 200) {
				// 파일의 내용을 업데이트
				if (selectedFile && selectedFile.id === file.id) {
					selectedFile.data.content = newContent;
				}
				
				// 메모 파일인 경우 콘텐츠 영역에 표시
				if (file.meta?.name?.toLowerCase().endsWith('.txt')) {
					contentType = 'memo';
				}
				
				toast.success($i18n.t('Content updated successfully.'));
			} else {
				toast.error($i18n.t('Failed to update content.'));
			}
		} catch (error) {
			console.error('콘텐츠 업데이트 오류:', error);
			toast.error($i18n.t('Failed to update content.'));
		}
	};

	// 파일명 변경 핸들러 함수 추가
	const renameFileHandler = async (fileId, newName) => {
		if (!fileId) return;
		
		try {
			console.log('파일명 변경:', newName);
			const response = await updateFileFilenameById(localStorage.token, fileId, newName);
			
			if (response && response.status === 200) {
				toast.success($i18n.t('File renamed successfully.'));
				
				// 파일 목록 새로고침
				await fetchAndUpdateFiles();
			} else {
				toast.error($i18n.t('Failed to rename file.'));
			}
		} catch (error) {
			console.error('파일명 변경 오류:', error);
			toast.error($i18n.t('Failed to rename file.'));
		}
	};

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
				<h1 class="{$mobile ? 'text-base sm:text-xl' : 'text-xl'} font-semibold mb-1 truncate flex items-center">
					{bookmark.company_name}
					{#if isShared && bookmark.bookmark_user_id && bookmark.bookmark_user_id !== currentUser?.id}
						{#await getUserInfo(bookmark.bookmark_user_id) then userInfo}
							<span class="ml-2 text-xs text-gray-500 bg-gray-50 dark:bg-gray-700 px-2 py-0.5 rounded-full whitespace-nowrap">
								공유자: {userInfo.name}
							</span>
						{/await}
					{/if}
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
				: ''} flex flex-col w-full mt-4 {$mobile ? 'h-auto' : 'h-[calc(100vh-8rem)]'}"
			class:mobile={$mobile}
		>
			<!-- 두 열 레이아웃으로 변경 -->
			<div class="flex-1 flex {$mobile ? 'flex-col' : 'flex-row'} h-full">
				<!-- 왼쪽 사이드바: 메모/첨부 목록 -->
				<div class="flex-shrink-0 {$mobile ? 'w-full mb-4' : 'w-72 max-w-72 pr-3'} flex flex-col gap-1 h-full">
					<!-- 메모 섹션 -->
					<div class="flex flex-col py-1 rounded-2xl border border-gray-50 dark:border-gray-850">
						<div class="px-3 py-1 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center cursor-pointer"
							on:click={() => showMemosSection = !showMemosSection}
						>
							<h2 class="text-sm font-medium">메모</h2>
							<button class="text-gray-500">
								{#if showMemosSection}
									<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
										<path fill-rule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clip-rule="evenodd" />
									</svg>
								{:else}
									<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
										<path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
									</svg>
								{/if}
							</button>
						</div>
						
						{#if showMemosSection}
							<div class="w-full flex flex-col">
								<div class="px-3">
									<div class="flex mb-0.5">
										<div class="self-center ml-1 mr-3">
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
											class="w-full text-sm pr-4 py-1 rounded-r-xl outline-none bg-transparent"
											bind:value={memoQuery}
											placeholder="메모 검색"
										/>
										
										<div>
											<button
												class="ml-1 px-2 py-1 text-sm rounded hover:bg-gray-100 dark:hover:bg-gray-800"
												on:click={() => {
													selectedFileId = null;
													selectedFile = null;
													setTimeout(() => {
														createAndUploadMemo('새 메모', '<p></p>');
													}, 50);
												}}
											>
												<svg 
													xmlns="http://www.w3.org/2000/svg" 
													viewBox="0 0 24 24" 
													fill="none" 
													stroke="currentColor" 
													stroke-width="2" 
													stroke-linecap="round" 
													stroke-linejoin="round" 
													class="size-5"
												>
													<path d="M12 5v14m-7-7h14" />
												</svg>
											</button>
										</div>
									</div>
								</div>

								{#if memoItems.length > 0}
									<div class="flex overflow-y-auto {$mobile ? 'max-h-48' : 'h-full'} w-full scrollbar-hidden text-xs">
										<!-- 메모 목록 커스텀 표시 -->
										<div class="w-full">
											{#each memoItems as memo}
												<div 
													class="mt-1 px-2 py-2 rounded-lg {selectedFileId === memo.id ? 'bg-gray-50 dark:bg-gray-850' : 'bg-transparent'} hover:bg-gray-50 dark:hover:bg-gray-850 transition flex justify-between cursor-pointer"
													on:click={() => {
														if (selectedFileId === memo.id) {
															closeContent();
														} else {
															selectedFile = null; // 먼저 파일 참조 초기화
															selectedFileId = memo.id;
															contentType = 'memo';
														}
													}}
												>
													<div class="flex items-center gap-2 overflow-hidden">
														<div class="font-medium text-sm truncate">
															{memo?.meta?.name ? memo.meta.name.replace('.txt', '') : '무제'}
														</div>
														<div class="text-xs text-gray-500 whitespace-nowrap">
															{memo.created_at ? formatDate(memo.created_at) : formatDate(new Date().toISOString())}
														</div>
													</div>
													<button 
														class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 self-center"
														on:click|stopPropagation={() => {
															if (selectedFileId === memo.id) {
																closeContent();
															}
															deleteFileHandler(memo.id);
														}}
													>
														<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
															<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
														</svg>
													</button>
												</div>
											{/each}
										</div>
									</div>
								{:else}
									<div class="my-3 flex flex-col justify-center text-center text-gray-500 text-xs">
										<div>
											메모가 없습니다
										</div>
									</div>
								{/if}
							</div>
						{/if}
					</div>

					<!-- 첨부파일 섹션 -->
					<div class="flex flex-col py-1 rounded-2xl border border-gray-50 dark:border-gray-850 mt-0.5">
						<div class="px-3 py-1 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center cursor-pointer"
							on:click={() => showFilesSection = !showFilesSection}
						>
							<h2 class="text-sm font-medium">첨부파일</h2>
							<button class="text-gray-500">
								{#if showFilesSection}
									<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
										<path fill-rule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clip-rule="evenodd" />
									</svg>
								{:else}
									<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
										<path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
									</svg>
								{/if}
							</button>
						</div>
						
						{#if showFilesSection}
							<div class="w-full flex flex-col">
								<div class="px-3">
									<div class="flex mb-0.5">
										<div class="self-center ml-1 mr-3">
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
											class="w-full text-sm pr-4 py-1 rounded-r-xl outline-none bg-transparent"
											bind:value={fileQuery}
											placeholder="파일 검색"
										/>

										<div>
											<button
												class="ml-1 px-2 py-1 text-sm rounded hover:bg-gray-100 dark:hover:bg-gray-800"
												on:click={() => {
													document.getElementById('files-input').click();
												}}
											>
												<svg 
													xmlns="http://www.w3.org/2000/svg" 
													viewBox="0 0 24 24" 
													fill="none" 
													stroke="currentColor" 
													stroke-width="2" 
													stroke-linecap="round" 
													stroke-linejoin="round" 
													class="size-5"
												>
													<path d="M12 5v14m-7-7h14" />
												</svg>
											</button>
										</div>
									</div>
								</div>

								{#if filteredItems.length > 0}
									<div class="flex overflow-y-auto {$mobile ? 'max-h-48' : 'h-full'} w-full scrollbar-hidden text-xs">
										<!-- 첨부파일 목록 커스텀 표시 -->
										<div class="w-full">
											{#each filteredItems as file}
												<div 
													class="mt-1 px-2 py-2 rounded-lg {selectedFileId === file.id ? 'bg-gray-50 dark:bg-gray-850' : 'bg-transparent'} hover:bg-gray-50 dark:hover:bg-gray-850 transition flex justify-between cursor-pointer"
													on:click={() => {
														if (selectedFileId === file.id) {
															closeContent();
														} else {
															selectedFile = null; // 먼저 파일 참조 초기화
															selectedFileId = file.id;
															contentType = 'file';
														}
													}}
												>
													<div class="flex-1 overflow-hidden">
														<div class="font-medium text-sm truncate">
															{file?.meta?.name || file?.name || '파일명 없음'}
														</div>
														<div class="flex items-center gap-2 text-xs text-gray-500">
															<span>{file.created_at ? formatDate(file.created_at) : ''}</span>
															<span>{formatFileSize(file?.size || file?.meta?.size || 0)}</span>
														</div>
													</div>
													<button 
														class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 self-center"
														on:click|stopPropagation={() => {
															if (selectedFileId === file.id) {
																closeContent();
															}
															deleteFileHandler(file.id);
														}}
													>
														<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
															<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
														</svg>
													</button>
												</div>
											{/each}
										</div>
									</div>
								{:else}
									<div class="my-3 flex flex-col justify-center text-center text-gray-500 text-xs">
										<div>
											첨부파일이 없습니다
										</div>
									</div>
								{/if}
							</div>
						{/if}
					</div>

					<!-- 채팅 리스트 섹션 -->
					{#if chatList && chatList.length > 0}
						<div class="flex flex-col border border-gray-50 dark:border-gray-850 rounded-2xl {$mobile ? 'mb-4' : 'mt-0.5'}">
							<div class="px-3 py-1 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center cursor-pointer"
								on:click={() => showChatsSection = !showChatsSection}
							>
								<h2 class="text-sm font-medium">채팅</h2>
								<button class="text-gray-500">
									{#if showChatsSection}
										<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
											<path fill-rule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clip-rule="evenodd" />
										</svg>
									{:else}
										<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
											<path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
										</svg>
									{/if}
								</button>
							</div>
							{#if showChatsSection}
								<div class="overflow-y-auto p-2">
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
							{/if}
						</div>
					{/if}
				</div>

				<!-- 오른쪽 콘텐츠 영역 -->
				<div class="flex-1 flex flex-col h-full {$mobile ? '' : 'ml-3'}">
					{#if showFileCloseButton}
						<div class="flex justify-end mb-2">
							<button 
								class="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 p-1"
								on:click={closeContent}
							>
								<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						</div>
					{/if}

					{#if contentType === 'company'}
						<!-- 기업 상세 정보 표시 -->
						<div class="p-4 space-y-2 h-full overflow-auto">				
							{#if isPrivateCompany}
								<!-- 비공개 기업 정보 표시 전용 컴포넌트 -->
								<PrivateCompanyDetail {bookmark} entityType={entityType} />
							{:else}
								<CompanyDetail company={bookmark} {financialData} />
							{/if}
						</div>
					{:else if contentType === 'file' && selectedFile}
						<!-- 파일 콘텐츠 표시 -->
						<div class="flex flex-col w-full h-full">
							<div class="shrink-0 mb-2 flex items-center">
								<div class="flex-1 text-xl font-medium">
									<span class="line-clamp-1">
										{selectedFile?.meta?.name || selectedFile?.name || '파일명 없음'}
									</span>
								</div>
							</div>

							<div class="flex-1 w-full h-full max-h-full bg-transparent outline-hidden overflow-y-auto scrollbar-hidden">
								{#if selectedFile?.meta?.name?.toLowerCase().endsWith('.jpg') || selectedFile?.meta?.name?.toLowerCase().endsWith('.jpeg') || selectedFile?.meta?.name?.toLowerCase().endsWith('.png') || selectedFile?.meta?.name?.toLowerCase().endsWith('.gif')}
									<!-- 이미지 파일인 경우 -->
									<div class="flex justify-center h-full">
										<img 
											src={`${WEBUI_API_BASE_URL}/files/${selectedFile.id}/content`} 
											alt={selectedFile?.meta?.name || selectedFile?.name} 
											class="object-contain"
											style="max-width: 100%; max-height: 100%;"
										/>
									</div>
								{:else if selectedFile?.meta?.name?.toLowerCase().endsWith('.pdf')}
									<!-- PDF 파일인 경우 -->
									<div class="h-full">
										<iframe 
											src={`${WEBUI_API_BASE_URL}/files/${selectedFile.id}/content`} 
											title={selectedFile?.meta?.name || selectedFile?.name}
											class="w-full h-full border-0"
										></iframe>
									</div>
								{:else if selectedFile?.data?.content}
									<!-- 텍스트 내용이 있는 경우 -->
									<div class="whitespace-pre-wrap p-4">
										{selectedFile.data.content}
									</div>
								{:else}
									<!-- 지원되지 않는 파일 타입 -->
									<div class="flex flex-col items-center justify-center h-full p-4">
										<div class="text-lg mb-4">
											{selectedFile?.meta?.name || selectedFile?.name || '파일명 없음'}
										</div>
									</div>
								{/if}
							</div>
						</div>
					{:else if contentType === 'memo' && selectedFile}
						<div class="flex-1 flex flex-col h-full">
							<div class="flex justify-between items-center w-full py-2 px-4 bg-white dark:bg-gray-900">
								<div class="text-lg font-medium truncate">
									<input 
										type="text"
										class="w-full bg-transparent border-none outline-none px-0 font-medium"
										value={selectedFile?.meta?.name ? selectedFile.meta.name.replace('.txt', '') : '무제'} 
										on:blur={(e) => {
											if (e.target.value.trim() !== '') {
												// 기존 이름과 다른 경우에만 업데이트
												const cleanedName = e.target.value.replace(/\.txt$/i, '');
												if (cleanedName !== selectedFile.meta.name.replace(/\.txt$/i, '')) {
													selectedFile.meta.name = cleanedName + '.txt';
													updateFileContentHandler();
												}
											}
										}}
									/>
								</div>
								<!-- <button 
									class="ml-2 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800"
									on:click={() => {
										selectedFileId = null;
										selectedFile = null;
										contentType = 'company';
									}}
								>
									<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
										<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
									</svg>
								</button> -->
							</div>
							<div class="flex-1 overflow-auto p-4">
								<NoteEditor 
									initialTitle={selectedFile?.meta?.name ? selectedFile.meta.name.replace('.txt', '') : '무제'}
									initialContent={selectedFile?.data?.content || '<p></p>'}
									selectedFile={selectedFile}
									on:change={(e) => {
										if (selectedFile && selectedFile.data) {
											selectedFile.data.content = e.detail;
											updateFileContent(selectedFile, e.detail);
										}
									}}
									on:titleChange={(e) => {
										if (selectedFile && selectedFile.meta) {
											const cleanedName = e.detail.replace(/\.txt$/i, '');
											selectedFile.meta.name = cleanedName + '.txt';
											updateFileContentHandler();
										}
									}}
								/>
							</div>
						</div>
					{:else if contentType === 'file' && selectedFile}
						<div class="flex-1 flex flex-col">
							<div class="flex justify-between items-center w-full py-2 px-4 bg-white dark:bg-gray-900 border-b dark:border-gray-700">
								<div class="text-lg font-medium truncate">
									<span>{selectedFile?.meta?.name || '파일'}</span>
								</div>
								<button 
									class="ml-2 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800"
									on:click={() => {
										selectedFileId = null;
										selectedFile = null;
										contentType = 'company';
									}}
								>
									<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
										<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
									</svg>
								</button>
							</div>
							<div class="flex-1 overflow-auto p-4">
								<!-- 파일 내용 표시 -->
								<iframe
									src={selectedFile?.url}
									title={selectedFile?.meta?.name || '파일'}
									class="w-full h-full border-0"
									sandbox="allow-scripts allow-same-origin"
								></iframe>
							</div>
						</div>
					{/if}
				</div>
			</div>
		</div>
	{:else}
		<Spinner />
	{/if}
</div>

<!-- 다른 모달들은 그대로 유지 -->
{#if showChatModal}
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
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.414-1.414L10 8.586l3.72-3.72a.75.75 0 10-1.414-1.414L10 10z"
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
{/if}
