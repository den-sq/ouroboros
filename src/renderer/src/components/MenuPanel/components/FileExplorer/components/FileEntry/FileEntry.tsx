import styles from './FileEntry.module.css'

import Folder from './assets/folder.svg?react'
import Image from './assets/image.svg?react'
import File from './assets/file.svg?react'
import { useDraggable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'

function FileEntry({ name, path, type }): JSX.Element {
	const { attributes, listeners, setNodeRef, transform } = useDraggable({
		id: path,
		data: {
			name,
			path,
			type,
			source: 'file-explorer'
		}
	})

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

	const style = {
		transform: CSS.Translate.toString(transform)
	}

	return (
		<div ref={setNodeRef} style={style} {...listeners} {...attributes}>
			<div className={styles.fileEntry} data-value={path}>
				<div className={styles.fileEntryIcon}>{icon}</div>
				<div className="file-explorer-font-size poppins-regular">{name}</div>
			</div>
		</div>
	)
}

export default FileEntry
