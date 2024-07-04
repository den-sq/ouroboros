import { useRef, useEffect, useState, useContext, ChangeEvent } from 'react'
import styles from './OptionEntry.module.css'
import { useDroppable } from '@dnd-kit/core'
import { DragContext } from '@renderer/App'

const MIN_WIDTH = 25
const LABEL_GAP = 15

// Types: number, string, boolean, droppable

function OptionEntry({ label, initialValue, inputType, minWidth = MIN_WIDTH }): JSX.Element {
	const inputRef = useRef<HTMLInputElement>(null)
	const labelRef = useRef<HTMLDivElement>(null)
	const [labelWidth, setLabelWidth] = useState(0)

	const [inputValue, setInputValue] = useState(initialValue)

	const inputName = label.toLowerCase().replaceAll(' ', '-')

	const { parentChildData } = useContext(DragContext)

	const { isOver, setNodeRef } = useDroppable({
		id: inputName
	})

	const style = {
		opacity: isOver && inputType == 'droppable' ? 0.5 : 1
	}

	let htmlInputType = 'text'

	switch (inputType) {
		case 'number':
			htmlInputType = 'number'
			break
		case 'string':
			htmlInputType = 'text'
			break
		case 'boolean':
			htmlInputType = 'checkbox'
			break
		case 'droppable':
			htmlInputType = 'text'
			break
		default:
			break
	}

	// Receive file paths dropped from FileExplorer
	useEffect(() => {
		if (parentChildData && parentChildData[0] === inputName && inputType === 'droppable') {
			const childData = parentChildData[1]?.data?.current

			if (childData && childData.source === 'file-explorer' && childData.type == 'file') {
				if (inputRef.current) {
					setInputValue(childData.path)

					resizeInput(childData.path)
				}
			}
		}
	}, [parentChildData])

	function resizeInput(value: string) {
		if (inputType === 'boolean') return

		if (labelRef.current) {
			const label = labelRef.current
			// Measure and store label width
			setLabelWidth(label.offsetWidth + LABEL_GAP)
		}

		if (inputRef.current) {
			const input = inputRef.current

			// Create a temporary span to measure text width
			const tempSpan = document.createElement('span')

			// Match input font size and family
			tempSpan.style.fontSize = getComputedStyle(input).fontSize
			tempSpan.style.fontFamily = getComputedStyle(input).fontFamily
			tempSpan.style.visibility = 'hidden' // Hide span
			tempSpan.textContent = value
			document.body.appendChild(tempSpan)

			// Set input width based on temp span width, with a minimum width
			input.style.width = `${Math.max(tempSpan.offsetWidth, minWidth)}px`
			document.body.removeChild(tempSpan)
		}
	}

	useEffect(() => {
		resizeInput(initialValue)
	}, [initialValue, minWidth])

	const onChange = (e: ChangeEvent<HTMLInputElement>) => {
		// Before or after?
		setInputValue(e.target.value)

		if (inputType === 'boolean') return
		if (!inputRef.current) return

		const target = e.target
		const parentWidth = target.parentElement?.offsetWidth || 0
		const maxWidth = parentWidth - labelWidth

		target.style.width = `${minWidth}px` // Reset width to minimum before calculating new width
		target.style.width = `${Math.min(target.scrollWidth, maxWidth)}px`
	}

	return (
		<div ref={setNodeRef} style={style}>
			<div className={`${styles.optionEntry} poppins-medium`}>
				<div
					ref={labelRef}
					className={`${styles.optionLabel} option-font-size ${isOver && inputType == 'droppable' ? 'poppins-bold' : ''}`}
				>
					{label}
				</div>
				<input
					name={inputName}
					ref={inputRef}
					type={htmlInputType}
					className={styles.optionInput}
					value={inputValue}
					onChange={onChange}
				/>
			</div>
		</div>
	)
}

export default OptionEntry
