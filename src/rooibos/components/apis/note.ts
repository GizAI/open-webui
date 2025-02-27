// note.ts
import { WEBUI_API_BASE_URL } from '$lib/constants';

export const getNote = async (id: string) => {
	let error = null;
  
	const res = await fetch(
	  `${WEBUI_API_BASE_URL}/rooibos/notes/${id}`,
	  {
		method: 'GET',
		headers: {
		  Accept: 'application/json',
		  'Content-Type': 'application/json',
		  authorization: `Bearer ${localStorage.token}`
		},
	  }
	)
	  .then(async (res) => {
		if (!res.ok) throw await res.json();
		const data = await res.json();
		return data.note;
	  })
	  .catch((err) => {
		error = err.detail;
		return null;
	  });
  
	if (error) {
	  throw error;
	}
  
	return res;
  };

export const createNote = async (token: string, newId: string, userId: string = '', folderId: string = '') => {
	let error = null;

	const queryParams = new URLSearchParams({
		newId: newId,
		userId: userId,
		folderId: folderId
	});

	const res = await fetch(`${WEBUI_API_BASE_URL}/rooibos/notes/add/?${queryParams.toString()}`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			name: name
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updateNote = async (
	token: string,
	noteId: string,
	newTitle: string,
	newContent: any
  ) => {
	let error = null;
  
	const queryParams = new URLSearchParams({ noteId });
	const res = await fetch(
	  `${WEBUI_API_BASE_URL}/rooibos/notes/update/?${queryParams.toString()}`,
	  {
		method: 'PUT',
		headers: {
		  Accept: 'application/json',
		  'Content-Type': 'application/json',
		  authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ title: newTitle, content: newContent })
	  }
	)
	  .then(async (res) => {
		if (!res.ok) throw await res.json();
		return res.json();
	  })
	  .catch((err) => {
		error = err.detail;
		return null;
	  });
  
	if (error) {
	  throw error;
	}
  
	return res;
  };
  
  
