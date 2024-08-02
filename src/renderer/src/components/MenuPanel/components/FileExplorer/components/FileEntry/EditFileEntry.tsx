import styles from './FileEntry.module.css'

import Folder from './assets/folder.svg?react'
import Image from './assets/image.svg?react'
import File from './assets/file.svg?react'
import { useEffect, useRef } from 'react'

function EditFileEntry({
	name,
	path,
	type,
	handleChange
}: {
	name: string
	path: string
	type: 'folder' | 'image' | 'file'
	handleChange: (event: InputEvent) => void
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

	const inputRef = useRef<HTMLInputElement>(null)

	useEffect(() => {
		if (inputRef.current) {
			inputRef.current.value = name

			// Focus the input
			inputRef.current.focus()
		}

		const listener = (event: Event): void => {
			if (inputRef.current) {
				handleChange(event as InputEvent)
			}
		}

		if (inputRef.current) {
			// Listen for when the input changes and loses focus
			inputRef.current.addEventListener('change', listener)
			inputRef.current.addEventListener('blur', listener)
		}

		return (): void => {
			if (inputRef.current) {
				inputRef.current.removeEventListener('change', listener)
				inputRef.current.removeEventListener('blur', listener)
			}
		}
	}, [inputRef])

	return (
		<div className={styles.fileEntry} data-value={path}>
			<div className={styles.fileEntryIcon}>{icon}</div>
			<input className={`${styles.fileEntryInput} poppins-regular`} ref={inputRef} />
		</div>
	)
}

export default EditFileEntry
