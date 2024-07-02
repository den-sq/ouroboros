import styles from './FileEntry.module.css'

import Folder from './assets/folder.svg?react'
import Image from './assets/image.svg?react'
import File from './assets/file.svg?react'

function FileEntry({ name, path = '', type = '' }): JSX.Element {
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
		<div className={styles.fileEntry}>
			<div className={styles.fileEntryIcon}>{icon}</div>
			<div className="file-explorer-font-size poppins-regular">{name}</div>
		</div>
	)
}

export default FileEntry
