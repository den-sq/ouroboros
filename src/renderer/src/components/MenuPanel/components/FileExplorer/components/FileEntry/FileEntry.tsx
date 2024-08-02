import styles from './FileEntry.module.css'

import Folder from './assets/folder.svg?react'
import Image from './assets/image.svg?react'
import File from './assets/file.svg?react'

function FileEntry({
	name,
	path,
	type,
	bold
}: {
	name: string
	path: string
	type: 'folder' | 'image' | 'file'
	bold?: boolean
}): JSX.Element {
	let icon: JSX.Element = <></>
	switch (type) {
		case 'folder':
			icon = <Folder />
			break
		case 'image':
			icon = <Image />
			break
		case 'file':
			icon = <File />
			break
		default:
			break
	}

	return (
		<div className={styles.fileEntry} data-value={path}>
			<div className={styles.fileEntryIcon}>{icon}</div>
			<div className={bold ? 'poppins-bold' : 'poppins-regular'}>{name}</div>
		</div>
	)
}

export default FileEntry
