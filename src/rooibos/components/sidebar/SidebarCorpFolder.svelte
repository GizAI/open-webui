<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { v4 as uuidv4 } from 'uuid';
	import { getContext } from 'svelte';
	import { user, showSidebar, mobile } from '$lib/stores';
	import { folderUpdateTrigger, triggerFolderUpdate } from '$rooibos/stores';
	import { createNewRooibosFolder, getRooibosFolders } from '$rooibos/components/apis/folder';
	import RooibosFolder from '$rooibos/components/folder/RooibosFolder.svelte';
	import RooibosFolderMenu from '$rooibos/components/folder/RooibosFolderMenu.svelte';

	// 폴더 인터페이스 정의
	interface RooibosFolder {
		id: string;
		name: string;
		parent_id: string | null;
		created_at: number;
		updated_at: number;
		type: string;
		childrenIds?: string[];
		isTrash?: boolean;
		isShared?: boolean;
	}

	interface RooibosFolders {
		[key: string]: RooibosFolder;
	}

    export let collapsible = true;
    export let open = true;
    
	const i18n = getContext('i18n');

	let rooibosFolders: RooibosFolders = {}; // 기업 전용 폴더 상태

	const initRooibosFolders = async () => {
		const folderList = await getRooibosFolders(localStorage.token, $user?.id).catch((error) => {
			toast.error(`${error}`);
			return [];
		});

		rooibosFolders = {};

		// 폴더 초기화
		for (const folder of folderList) {
			rooibosFolders[folder.id] = { ...(rooibosFolders[folder.id] || {}), ...folder };
		}

		// 부모-자식 관계 설정
		for (const folder of folderList) {
			if (folder.parent_id) {
				if (!rooibosFolders[folder.parent_id]) {
					rooibosFolders[folder.parent_id] = {
						id: folder.parent_id,
						name: '',
						parent_id: null,
						created_at: Date.now(),
						updated_at: Date.now(),
						type: 'corp'
					}; // 부모 폴더가 없으면 생성
				}

				rooibosFolders[folder.parent_id].childrenIds = rooibosFolders[folder.parent_id].childrenIds
					? [...rooibosFolders[folder.parent_id].childrenIds, folder.id]
					: [folder.id];

				// 업데이트 시간 기준으로 정렬
				if (rooibosFolders[folder.parent_id].childrenIds) {
					rooibosFolders[folder.parent_id].childrenIds.sort((a: string, b: string) => {
						return rooibosFolders[b].updated_at - rooibosFolders[a].updated_at;
					});
				}
			}
		}

		const trashId = 'trash-folder-' + ($user?.id || '');
		rooibosFolders[trashId] = {
			id: trashId,
			name: '휴지통',
			parent_id: null,
			created_at: Date.now(),
			updated_at: Date.now(),
			type: 'corp',
			isTrash: true
		};

		const sharedId = 'shared-folder-' + ($user?.id || '');
		rooibosFolders[sharedId] = {
			id: sharedId,
			name: '공유받은 기업',
			parent_id: null,
			created_at: Date.now(),
			updated_at: Date.now(),
			type: 'corp',
			isShared: true
		};
	};

	const createRooibosFolder = async (name = 'Untitled', type = 'corp') => {
		if (name === '') {
			toast.error($i18n.t('Folder name cannot be empty.'));
			return;
		}

		const rootFolders = Object.values(rooibosFolders).filter((folder: RooibosFolder) => folder.parent_id === null && folder.type === type);
		if (rootFolders.find((folder: RooibosFolder) => folder.name.toLowerCase() === name.toLowerCase())) {
			let i = 1;
			while (
				rootFolders.find((folder: RooibosFolder) => folder.name.toLowerCase() === `${name} ${i}`.toLowerCase())
			) {
				i++;
			}
			name = `${name} ${i}`;
		}

		// 임시 폴더 추가
		const tempId = uuidv4();
		rooibosFolders = {
			...rooibosFolders,
			[tempId]: {
				id: tempId,
				name: name,
				created_at: Date.now(),
				updated_at: Date.now(),
				type: type,
				parent_id: null
			}
		};

		const res = await createNewRooibosFolder(localStorage.token, name, $user?.id, type).catch(
			(error) => {
				toast.error(`${error}`);
				return null;
			}
		);

		if (res) {
			// 폴더가 생성되면 전역 트리거 업데이트
			triggerFolderUpdate();
			await initRooibosFolders();
		}
	};

	const handleFolderDelete = async (event) => {
		await initRooibosFolders();
	};
	
	// 폴더 클릭 시 모바일에서 사이드바 접기
	const handleFolderClick = () => {
		if ($mobile) {
			showSidebar.set(false);
		}
	};

	// 폴더 업데이트 감지 구독
	folderUpdateTrigger.subscribe(async () => {
		await initRooibosFolders();
	});

	// 초기 폴더 로드
	initRooibosFolders();
</script>

<RooibosFolder
	collapsible={collapsible}
	className="px-2 mt-0.5"
	name="나의 고객"
	onAdd={() => createRooibosFolder('Untitled', 'corp')}
	onAddLabel={$i18n.t('New Folder')}
	open={open}
>
	<RooibosFolderMenu
		folders={Object.values(rooibosFolders)
			.filter((folder) => folder.type === 'corp')
			.reduce((acc, folder) => {
				acc[folder.id] = folder;
				return acc;
			}, {})}
		parentId={null}
		on:delete={handleFolderDelete}
		on:folderClick={handleFolderClick}
	/>
</RooibosFolder> 