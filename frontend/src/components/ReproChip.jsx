// ReproChip.jsx — Chip for reproducibility status
import Chip from './Chip'

export default function ReproChip({ status }) {
  if (status === 'pass')
    return <Chip color="#22C55E" bg="rgba(20,83,45,0.13)" border="#22C55E">✓ REPRODUCED</Chip>
  if (status === 'fail')
    return <Chip color="#EF4444" bg="rgba(69,10,10,0.13)" border="#EF4444">✗ NOT REPRODUCED</Chip>
  if (status === 'error')
    return <Chip color="#F59E42" bg="rgba(120,53,15,0.13)" border="#F59E42">! ERROR</Chip>
  return null
}
