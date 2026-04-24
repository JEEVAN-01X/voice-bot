import { useEffect, useState } from 'react';
import { collection, onSnapshot, orderBy, query } from 'firebase/firestore';
import { db } from './firebase';
import OrderCard from './OrderCard';

export default function Dashboard() {
  const [orders, setOrders] = useState([]);
  const [filter, setFilter] = useState('all');
  const [phone, setPhone] = useState('');
  const [calling, setCalling] = useState(false);

  useEffect(() => {
    const q = query(collection(db,'orders'), orderBy('confirmed_at','desc'));
    const unsub = onSnapshot(q, snap => {
      setOrders(snap.docs.map(d => ({ id: d.id, ...d.data() })));
    });
    return () => unsub();
  }, []);

  const triggerCall = async () => {
    if (!phone) return;
    setCalling(true);
    await fetch(`${import.meta.env.VITE_API_URL}/make-call?to=${phone}`, { method: 'POST' });
    setCalling(false);
  };

  const filtered = filter === 'all' ? orders : orders.filter(o => o.language === filter);
  const counts = { total: orders.length, confirmed: orders.filter(o=>o.status==='confirmed').length };

  return (
    <div className='p-6 bg-gray-50 min-h-screen'>
      <h1 className='text-2xl font-bold text-blue-900 mb-1'>Automaton AI — Order Dashboard</h1>
      <p className='text-sm text-gray-500 mb-4'>Live order feed · {counts.total} total · {counts.confirmed} confirmed</p>

      <div className='bg-white rounded-xl border p-4 mb-6 flex gap-3 items-center shadow-sm'>
        <input
          className='border rounded-lg px-3 py-2 text-sm flex-1'
          placeholder='+919876543210'
          value={phone}
          onChange={e => setPhone(e.target.value)}
        />
        <button
          onClick={triggerCall}
          disabled={calling}
          className='bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50'>
          {calling ? 'Calling...' : '📞 Trigger Call'}
        </button>
      </div>

      <div className='flex gap-2 mb-6'>
        {['all','en-IN','hi-IN','kn-IN','mr-IN'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded-full text-sm font-medium ${filter===f ? 'bg-blue-600 text-white' : 'bg-white border text-gray-600'}`}>
            {f === 'all' ? 'All' : f.split('-')[0].toUpperCase()}
          </button>
        ))}
      </div>

      <div className='grid gap-4'>
        {filtered.length === 0
          ? <p className='text-gray-400 text-sm'>No orders yet. Trigger a call to get started!</p>
          : filtered.map(o => <OrderCard key={o.id} order={o} />)}
      </div>
    </div>
  );
}
