<script lang="ts">
	import Fuse from 'fuse.js';
	import { toast } from 'svelte-sonner';
	import { v4 as uuidv4 } from 'uuid';

	import { onMount, getContext, onDestroy, tick } from 'svelte';
	const i18n = getContext('i18n');

	import { page } from '$app/stores';
	import { showSidebar, knowledge as _knowledge } from '$lib/stores';

	import { updateFileDataContentById, uploadFile } from '$lib/apis/files';

	import { transcribeAudio } from '$lib/apis/audio';
	import { blobToFile } from '$lib/utils';

	import Spinner from '$lib/components/common/Spinner.svelte';
	import Files from './CorpBookmarksBase/Files.svelte';
	import AddFilesPlaceholder from '$lib/components/AddFilesPlaceholder.svelte';

	import AddContentMenu from './CorpBookmarksBase/AddContentMenu.svelte';
	import AddTextContentModal from './CorpBookmarksBase/AddTextContentModal.svelte';

	import SyncConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import RichTextInput from '$lib/components/common/RichTextInput.svelte';
	import Drawer from '$lib/components/common/Drawer.svelte';
	import ChevronLeft from '$lib/components/icons/ChevronLeft.svelte';
	import LockClosed from '$lib/components/icons/LockClosed.svelte';
	import AccessControlModal from '$lib/components/workspace/common/AccessControlModal.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	
	import BookOpen from '$lib/components/icons/BookOpen.svelte';


	let largeScreen = true;

	let pane: any;
	let showSidepanel = true;
	let minSize = 0;

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
		smtp_id: string;
		latitude: string;
		longitude: string;
		bookmark_id?: string | null;    
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
		certificate_expiry_date?: string;
		sme_type?: string;
		cri_company_size?: string;
		lab_name?: string;
		first_approval_date?: string;
		lab_location?: string;
		research_field?: string;
		division?: string;
		birth_year?: string;
		foundation_year?: string;
		family_shareholder_yn?: string;
		external_shareholder_yn?: string;
		financial_statement_year?: string;
		employees?: number;
		venture_confirmation_type?: string;
		svcl_region?: string;
		venture_valid_from?: string;
		venture_valid_until?: string;
		confirming_authority?: string;
		new_reconfirmation_code?: string;
		postal_code?: string;
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

	let id: any = null;
	let bookmark: Bookmark | null = null;
	let financialData: FinancialData | null = null;
	let query = '';

	let showAddTextContentModal = false;
	let showSyncConfirmModal = false;
	let showAccessControlModal = false;

	let inputFiles : any= null;

	let filteredItems: any = [];
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

	let selectedFile: any = null;
	let selectedFileId: any = null;

	$: if (selectedFileId) {
		const file = (bookmark?.files ?? []).find((file) => file.id === selectedFileId);
		if (file) {
			file.data = file.data ?? { content: '' };
			selectedFile = file;
		} else {
			selectedFile = null;
		}
	} else {
		selectedFile = null;
	}

	let fuse: any = null;
	let debounceTimeout: any = null;
	let mediaQuery: any;
	let dragged = false;

	const createFileFromText = (name: string, content: string) => {
		const blob = new Blob([content], { type: 'text/plain' });
		const file = blobToFile(blob, `${name}.txt`);

		console.log(file);
		return file;
	};

	const uploadFileHandler = async (file: any) => {
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

		if (fileItem.size == 0) {
			toast.error($i18n.t('You cannot upload an empty file.'));
			return null;
		}

		bookmark.files = [...(bookmark.files ?? []), fileItem];

		// Check if the file is an audio file and transcribe/convert it to text file
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
			const uploadedFile = await uploadFile(localStorage.token, file).catch((e) => {
				toast.error(e);
				return null;
			});

			if (uploadedFile) {
				bookmark.files = bookmark.files.map((item) => {
					if (item.itemId === tempItemId) {
						item.id = uploadedFile.id;
					}

					delete item.itemId;
					return item;
				});
				await addFileHandler(uploadedFile.id);
			} else {
				toast.error($i18n.t('Failed to upload file.'));
			}
		} catch (e) {
			toast.error(e);
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
					const files = Array.from(input.files)
						.filter((file) => !hasHiddenFolder(file.webkitRelativePath));

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

	// Helper function to maintain file paths within zip
	const syncDirectoryHandler = async () => {
		if ((bookmark?.files ?? []).length > 0) {
			const res = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/${id}/file/reset`, {
				method: 'POST',
				headers: {
					Accept: 'application/json',
					'Content-Type': 'application/json'
				}
			})

			if (res) {
				toast.success($i18n.t('Bookmark reset successfully.'));

				// Upload directory
				uploadDirectoryHandler();
			}
		} else {
			uploadDirectoryHandler();
		}
	};

	const addFileHandler = async (fileId: string) => {
		const res = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/${id}/file/add`, {
			method: 'POST',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				file_id: fileId
			})
		})

		if (res.ok) {
			const data = await res.json();
			bookmark = data.data[0];
			filteredItems = data.data[0].files;
			toast.success($i18n.t('File added successfully.'));
		} else {
			toast.error($i18n.t('Failed to add file.'));
		}
	};

	const deleteFileHandler = async (fileId: string) => {
		const res = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/${id}/file/remove`, {
			method: 'POST',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				file_id: fileId
			})
		})

		if (res.ok) {
			filteredItems = filteredItems.filter(item => item.id !== fileId);
			toast.success($i18n.t('File removed successfully.'));
		}
	};

	const updateFileContentHandler = async () => {
		const fileId = selectedFile.id;
		const content = selectedFile.data.content;

		const res = await updateFileDataContentById(localStorage.token, fileId, content).catch((e) => {
			toast.error(e);
		});

		if (res) {
			toast.success($i18n.t('File content updated successfully.'));
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

			// const res = await updateKnowledgeById(localStorage.token, id, {
			// 	...bookmark,
			// 	name: bookmark?.company_name,
			// 	description: bookmark?.description,
			// 	access_control: bookmark.access_control
			// }).catch((e) => {
			// 	toast.error(e);
			// });

			// if (res) {
			// 	toast.success($i18n.t('bookmark updated successfully'));
			// 	_knowledge.set(await getKnowledgeBases(localStorage.token));
			// }
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

		// Check if a file is being draggedOver.
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
		// listen to resize 1024px
		mediaQuery = window.matchMedia('(min-width: 1024px)');

		mediaQuery.addEventListener('change', handleMediaQuery);
		handleMediaQuery(mediaQuery);

		// Select the container element you want to observe
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

		const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/${id}`, {
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				authorization: `Bearer ${localStorage.token}`
			}
		})

		const company_id = $page.url.searchParams.get("company_id")
		const financialResponse = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/${company_id}/financialData`, {
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				authorization: `Bearer ${localStorage.token}`
			}
		})

		const data = await response.json();
		bookmark = data.data[0];

		const filnancial = await financialResponse.json();
		financialData = filnancial.data;

		filteredItems = bookmark?.files ?? [];

		const dropZone = document.querySelector('body');
		dropZone?.addEventListener('dragover', onDragOver);
		dropZone?.addEventListener('drop', onDrop);
		dropZone?.addEventListener('dragleave', onDragLeave);
	});

	onDestroy(() => {
		mediaQuery?.removeEventListener('change', handleMediaQuery);
		const dropZone = document.querySelector('body');
		dropZone?.removeEventListener('dragover', onDragOver);
		dropZone?.removeEventListener('drop', onDrop);
		dropZone?.removeEventListener('dragleave', onDragLeave);
	});

	const metrics = [
		{ name: '매출액', key: 'revenue' },
		{ name: '당기순이익', key: 'net_income' },
		{ name: '영업이익', key: 'operating_income' },
		{ name: '총자산', key: 'total_assets' },
		{ name: '총부채', key: 'total_liabilities' },
		{ name: '총자본', key: 'total_equity' },
		{ name: '자본금', key: 'capital_stock' },
		{ name: '법인세', key: 'corporate_tax' },
		{ name: '유동자산', key: 'current_assets' },
		{ name: '당좌자산', key: 'quick_assets' },
		{ name: '재고자산', key: 'inventory' },
		{ name: '비유동자산', key: 'non_current_assets' },
		{ name: '투자자산', key: 'investment_assets' },
		{ name: '유형자산', key: 'tangible_assets' },
		{ name: '무형자산', key: 'intangible_assets' },
		{ name: '유동부채', key: 'current_liabilities' },
		{ name: '비유동부채', key: 'non_current_liabilities' },
		{ name: '이익잉여금', key: 'retained_earnings' },
		{ name: '이익', key: 'profit' },
		{ name: '매출원가', key: 'sales_cost' },
		{ name: '매출총이익', key: 'sales_profit' },
		{ name: '판매관리비', key: 'sga' },
		{ name: '기타수익', key: 'other_income' },
		{ name: '기타비용', key: 'other_expenses' },
		{ name: '세전이익', key: 'pre_tax_income' }
	];

	const years = ['2023', '2022', '2021'];
	let showAllMetrics = false;
	
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

<AddTextContentModal
	bind:show={showAddTextContentModal}
	on:submit={(e) => {
		const file = createFileFromText(e.detail.name, e.detail.content);
		uploadFileHandler(file);
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

<div class="flex flex-col w-full translate-y-1" id="collection-container">
	{#if id && bookmark}
		<AccessControlModal
			bind:show={showAccessControlModal}
			bind:accessControl={bookmark.access_control}
			onChange={() => {
				changeDebounceHandler();
			}}
		/>
		<div class="w-full mb-2.5">
			<!-- 상위 컨테이너를 flex-col로 설정하여 세로 정렬 -->
			<div class="flex flex-col w-full px-6 py-4 overflow-y-auto space-y-6">
				<div class="flex items-center justify-between w-full px-0.5 mb-1">
					<div class="w-full">
						<input
							type="text"
							class="text-left w-full font-semibold text-2xl font-primary bg-transparent outline-none"
							bind:value={bookmark.company_name}
							placeholder="Bookmark Company Name"
							readonly
						/>
					</div>

					<!-- <div class="self-center flex-shrink-0">
						<button
							class="bg-gray-50 hover:bg-gray-100 text-black dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-white transition px-2 py-1 rounded-full flex gap-1 items-center"
							type="button"
							on:click={() => {
								showAccessControlModal = true;
							}}
						>
							<LockClosed strokeWidth="2.5" className="size-3.5" />

							<div class="text-sm font-medium flex-shrink-0">
								{$i18n.t('Access')}
							</div>
						</button>
					</div> -->
				</div>

			  <!-- 기본 정보 섹션 -->
			  <div class="space-y-2">
				<h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
				  <MapPin size={16} class="text-blue-500" />
				  기본 정보
				</h3>
				<div class="space-y-1">
				  {#if bookmark.business_registration_number}
					<p class="text-sm text-gray-600 flex items-center gap-2">
					  <Briefcase size={16} class="text-green-500" />
					  사업자 등록 번호: {bookmark.business_registration_number}
					</p>
				  {/if}				  {#if bookmark.corporate_number}
					<p class="text-sm text-gray-600 flex items-center gap-2">
						<Briefcase size={16} class="text-orange-500" />
						법인등록번호: {bookmark.corporate_number}
					</p>
				  {/if}
			
				  {#if bookmark.representative}
					<p class="text-sm text-gray-600 flex items-center gap-2">
					  <Users size={16} class="text-purple-500" />
					  대표이사: {bookmark.representative}
					  {#if bookmark.birth_year}
						({bookmark.birth_year})
					  {/if}
					</p>
				  {/if}
			
				  {#if bookmark.address}
					<p class="text-sm text-gray-600 flex items-center gap-2">
					  <MapPin size={16} class="text-red-500" />
					  주소: {bookmark.address}
					</p>
				  {/if}

				  {#if bookmark.cri_company_size}
					<p class="text-sm text-gray-600 flex items-center gap-2">
					  <Phone size={16} class="text-indigo-500" />
					  기업규모: {bookmark.cri_company_size}
					</p>
				  {/if}
			
				  {#if bookmark.phone_number}
					<p class="text-sm text-gray-600 flex items-center gap-2">
					  <Phone size={16} class="text-indigo-500" />
					  전화번호: {bookmark.phone_number}
					</p>
				  {/if}

				  {#if bookmark.establishment_date}
					<p class="text-sm text-gray-600 flex items-center gap-2">
					  <Calendar size={16} class="text-pink-500" />
					  설립일: {String(bookmark.establishment_date).replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3')}
					</p>
				  {/if}
			
				  {#if bookmark.employee_count}
					<p class="text-sm text-gray-600 flex items-center gap-2">
					  <Users size={16} class="text-purple-500" />
					  임직원 수: {bookmark.employee_count}명
					</p>
				  {/if}

				  {#if bookmark.fiscal_month}
					<p class="text-sm text-gray-600 flex items-center gap-2">
						<Calendar size={16} class="text-purple-500" />
						결산월: {bookmark.fiscal_month}월
					</p>
				  {/if}
				  {#if bookmark.main_bank}
					<p class="text-sm text-gray-600 flex items-center gap-2">
						<DollarSign size={16} class="text-green-500" />
						주거래은행: {bookmark.main_bank}
					</p>
				  {/if}	
			
				  {#if bookmark.website}
					<p class="text-sm text-gray-600 flex items-center gap-2">
					  <Globe size={16} class="text-yellow-500" />
					  웹사이트:
					  <a
						href={
						  bookmark.website.startsWith("http")
							? bookmark.website
							: `https://${bookmark.website}`
						}
						target="_blank"
						rel="noopener noreferrer"
						class="text-blue-500 underline"
					  >
						{bookmark.website.startsWith("http")
						  ? bookmark.website
						  : `https://${bookmark.website}`}
					  </a>
					</p>
				  {/if}
				</div>
			  </div>
			
			  <!-- 업종 정보 섹션 -->
			  {#if bookmark.industry}
				<div class="space-y-2">
				  <h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
					<Briefcase size={16} class="text-blue-500" />
					업종 정보
				  </h3>
				  {#if bookmark.industry_major}
					<p class="text-sm text-gray-600">업종: {bookmark.industry}</p>
				  {/if}
				  {#if bookmark.main_product}
					<p class="text-sm text-gray-600">주요상품: {bookmark.main_product}</p>
				  {/if}
				</div>
			  {/if}

			  {#if bookmark.family_shareholder_yn || bookmark.external_shareholder_yn}
				<div class="space-y-2">
					<h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
					<Users size={16} class="text-yellow-500" />
					주주 정보
					</h3>
					<div class="space-y-1">
					{#if bookmark.family_shareholder_yn}
						<p class="text-sm text-gray-600 flex items-center gap-2">
						<Users size={16} class="text-purple-500" />
						가족주주: {bookmark.family_shareholder_yn === 'Y' ? '있음' : '없음'}
						</p>
					{/if}
					{#if bookmark.external_shareholder_yn}
						<p class="text-sm text-gray-600 flex items-center gap-2">
						<Users size={16} class="text-blue-500" />
						외부주주: {bookmark.external_shareholder_yn === 'Y' ? '있음' : '없음'}
						</p>
					{/if}
					</div>
				</div>
				{/if}

			  <!-- 연구소 정보 섹션 추가 -->
			  {#if bookmark.lab_name || bookmark.research_field || bookmark.division}
				<div class="space-y-2">
					<h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
					<Microscope size={16} class="text-indigo-500" />
					연구소 정보
					</h3>
					<div class="space-y-1">
					{#if bookmark.lab_name}
						<p class="text-sm text-gray-600 flex items-center gap-2">
						<Building2 size={16} class="text-blue-500" />
						연구소명: {bookmark.lab_name}
						</p>
					{/if}
					{#if bookmark.research_field}
						<p class="text-sm text-gray-600 flex items-center gap-2">
						<FlaskConical size={16} class="text-green-500" />
						연구분야: {bookmark.research_field}
						</p>
					{/if}
					{#if bookmark.first_approval_date}
						<p class="text-sm text-gray-600 flex items-center gap-2">
						<CalendarCheck size={16} class="text-orange-500" />
						최초인정일: {bookmark.first_approval_date}
						</p>
					{/if}
					{#if bookmark.lab_location}
						<p class="text-sm text-gray-600 flex items-center gap-2">
						<MapPin size={16} class="text-red-500" />
						연구소 위치: {bookmark.lab_location}
						</p>
					{/if}
					{#if bookmark.division}
						<p class="text-sm text-gray-600 flex items-center gap-2">
						<ClipboardList size={16} class="text-purple-500" />
						연구소 구분: {bookmark.division}
						</p>
					{/if}
					</div>
				</div>
				{/if}


			  <!-- 인증 정보 섹션 -->
			  {#if bookmark.venture_confirmation_type || bookmark.research_field}
              <div class="space-y-2">
                <h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Award size={16} class="text-purple-500" />
                  인증 정보
                </h3>
                <div class="space-y-1">
                  {#if bookmark.sme_type}
                    <p class="text-sm text-gray-600 flex items-center gap-2">
                      <Award size={16} class="text-yellow-500" />
                      인증 유형: {bookmark.sme_type}
                    </p>
                  {/if}

                  {#if bookmark.certificate_expiry_date}
                    <p class="text-sm text-gray-600 flex items-center gap-2">
                      <Calendar size={16} class="text-orange-500" />
                      인증 만료일: {bookmark.certificate_expiry_date}
                    </p>
                  {/if}

				  {#if bookmark.venture_confirmation_type}
                    <p class="text-sm text-gray-600 flex items-center gap-2">
                      <Award size={16} class="text-green-500" />
                      벤처기업 인증: {bookmark.venture_confirmation_type}
                    </p>
                  {/if}

				  {#if bookmark.venture_valid_from || bookmark.venture_valid_until || bookmark.confirming_authority || bookmark.new_reconfirmation_code}
					<p class="text-sm text-gray-600 flex items-center gap-2">
						<CalendarCheck size={16} class="text-blue-500" />
						벤처 유효기간: {bookmark.venture_valid_from} ~ {bookmark.venture_valid_until}
					</p>
					<p class="text-sm text-gray-600 flex items-center gap-2">
						<Building2 size={16} class="text-indigo-500" />
						확인기관: {bookmark.confirming_authority}
					</p>
					<p class="text-sm text-gray-600 flex items-center gap-2">
						<List size={16} class="text-emerald-500" />
						재확인코드: {bookmark.new_reconfirmation_code}
					</p>
					{/if}
                	</div>
				</div>
				{/if}
			</div>
			  
			{#if financialData && Array.isArray(financialData) && financialData.length > 0}
			<div class="px-4 py-4 w-full">
				<table class="w-full text-sm">
					<thead>
					<tr class="border-b border-gray-200">
						<th class="sm:block text-left px-2 font-medium text-gray-600">
						<div class="sm:inline-block">재무정보</div>
						<div class="sm:inline-block sm:ml-2 text-xs text-gray-500">단위: 백만원</div>
						<button
							class="mt-1 sm:mt-0 sm:ml-2 inline-flex items-center px-2 py-1 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 text-xs"
							on:click={() => (showAllMetrics = !showAllMetrics)}
						>
							{#if showAllMetrics} 접기 {:else} 더보기 {/if}
						</button>
						</th>
						{#each years as year}
						<th class="w-1/5 text-right px-2 py-2 font-medium text-gray-600 whitespace-nowrap">
							{year}년
						</th>
						{/each}
					</tr>
					</thead>
					<tbody class="text-gray-600">
					{#if showAllMetrics}
						{#each metrics as metric}
						<tr class="border-b border-gray-100 hover:bg-gray-50">
							<td class="w-1/3 px-2 py-2 font-medium">{metric.name}</td>
							{#each years as year}
							{@const data = financialData.find(d => d.year == year)}
							<td class="w-1/5 text-right px-2 py-2">
								{#if data && data[metric.key] != null}
								<span class={`${data[metric.key] < 0 ? 'text-red-500' : ''} whitespace-nowrap`}>
									{new Intl.NumberFormat('ko-KR').format(data[metric.key])}
								</span>
								{:else}
								-
								{/if}
							</td>
							{/each}
						</tr>
						{/each}
					{:else}
						{#each metrics.slice(0, 7) as metric}
						<tr class="border-b border-gray-100 hover:bg-gray-50">
							<td class="w-1/3 px-2 py-2 font-medium">{metric.name}</td>
							{#each years as year}
							{@const data = financialData.find(d => d.year == year)}
							<td class="w-1/5 text-right px-2 py-2">
								{#if data && data[metric.key] != null}
								<span class={`${data[metric.key] < 0 ? 'text-red-500' : ''} whitespace-nowrap`}>
									{new Intl.NumberFormat('ko-KR').format(data[metric.key])}
								</span>
								{:else}
								-
								{/if}
							</td>
							{/each}
						</tr>
						{/each}
					{/if}
					</tbody>
				</table>
			</div>
			{/if}
		</div>

		<div class="flex flex-row flex-1 h-full max-h-full pb-2.5 gap-3">
			{#if largeScreen}
				<div class="flex-1 flex justify-start w-full h-full max-h-full">
					{#if selectedFile}
						<div class=" flex flex-col w-full h-full max-h-full">
							<div class="flex-shrink-0 mb-2 flex items-center">
								{#if !showSidepanel}
									<div class="-translate-x-2">
										<button
											class="w-full text-left text-sm p-1.5 rounded-lg dark:text-gray-300 dark:hover:text-white hover:bg-black/5 dark:hover:bg-gray-850"
											on:click={() => {
												pane.expand();
											}}
										>
											<ChevronLeft strokeWidth="2.5" />
										</button>
									</div>
								{/if}

								<div class=" flex-1 text-xl font-medium">
									<a
										class="hover:text-gray-500 hover:dark:text-gray-100 hover:underline flex-grow line-clamp-1"
										href={selectedFile.id ? `/api/v1/files/${selectedFile.id}/content` : '#'}
										target="_blank"
									>
										{selectedFile?.meta?.name}
									</a>
								</div>

								<div>
									<button
										class="self-center w-fit text-sm py-1 px-2.5 dark:text-gray-300 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 rounded-lg"
										on:click={() => {
											updateFileContentHandler();
										}}
									>
										{$i18n.t('Save')}
									</button>
								</div>
							</div>

							<div
								class=" flex-1 w-full h-full max-h-full text-sm bg-transparent outline-none overflow-y-auto scrollbar-hidden"
							>
								{#key selectedFile.id}
									<RichTextInput
										className="input-prose-sm"
										bind:value={selectedFile.data.content}
										placeholder={$i18n.t('Add content here')}
										preserveBreaks={true}
									/>
								{/key}
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
				<Drawer
					className="h-full"
					show={selectedFileId !== null}
					on:close={() => {
						selectedFileId = null;
					}}
				>
					<div class="flex flex-col justify-start h-full max-h-full p-2">
						<div class=" flex flex-col w-full h-full max-h-full">
							<div class="flex-shrink-0 mt-1 mb-2 flex items-center">
								<div class="mr-2">
									<button
										class="w-full text-left text-sm p-1.5 rounded-lg dark:text-gray-300 dark:hover:text-white hover:bg-black/5 dark:hover:bg-gray-850"
										on:click={() => {
											selectedFileId = null;
										}}
									>
										<ChevronLeft strokeWidth="2.5" />
									</button>
								</div>
								<div class=" flex-1 text-xl line-clamp-1">
									{selectedFile?.meta?.name}
								</div>

								<div>
									<button
										class="self-center w-fit text-sm py-1 px-2.5 dark:text-gray-300 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 rounded-lg"
										on:click={() => {
											updateFileContentHandler();
										}}
									>
										{$i18n.t('Save')}
									</button>
								</div>
							</div>

							<div
								class=" flex-1 w-full h-full max-h-full py-2.5 px-3.5 rounded-lg text-sm bg-transparent overflow-y-auto scrollbar-hidden"
							>
								{#key selectedFile.id}
									<RichTextInput
										className="input-prose-sm"
										bind:value={selectedFile.data.content}
										placeholder={$i18n.t('Add content here')}
										preserveBreaks={true}
									/>
								{/key}
							</div>
						</div>
					</div>
				</Drawer>
			{/if}

			<div
				class="{largeScreen ? 'flex-shrink-0 w-72 max-w-72' : 'flex-1'}
			flex
			py-2
			rounded-2xl
			border
			border-gray-50
			h-full
			dark:border-gray-850"
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
									placeholder={$i18n.t('Search Collection')}
									on:focus={() => {
										selectedFileId = null;
									}}
								/>

								<div>
									<AddContentMenu
										on:upload={(e) => {
											if (e.detail.type === 'directory') {
												uploadDirectoryHandler();
											} else if (e.detail.type === 'text') {
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
		</div>
	{:else}
		<Spinner />
	{/if}
</div>
