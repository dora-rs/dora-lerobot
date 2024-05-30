use dora_node_api::{dora_core::config::DataId, DoraNode, IntoArrow, MetadataParameters};
use eyre::Result;
use rustypot::{device::xl330, DynamixelSerialIO};
use serialport::SerialPort;
use std::{
    sync::mpsc,
    time::{Duration, Instant},
};

static _MAX_MASTER_GRIPER: u32 = 2554;
static _MAX_PUPPET_GRIPER: u32 = 3145;

static _MIN_MASTER_GRIPER: u32 = 1965;
static _MIN_PUPPET_GRIPER: u32 = 2500;
use clap::Parser;

const SERVOS: &'static [u8] = &[1, 2, 3, 4, 5, 6];
const NUM_SERVOS: usize = 6;
const GRIPPER_ID: u8 = 6;

/// Simple aloha teleop program for recording data
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    #[arg(short, long, default_value = "/dev/ttyACM1")]
    master_path: String,

    #[arg(short, long, default_value = "/dev/ttyACM0")]
    puppet_path: String,

    #[arg(long, default_value = "70")]
    strength: u16,

    #[arg(long, default_value = "1000000")]
    master_baudrate: u32,

    #[arg(long, default_value = "1000000")]
    puppet_baudrate: u32,
}

enum State {
    Position(Vec<f64>),
    Velocity(Vec<f64>),
    Current(Vec<u16>),
    GoalPosition(Vec<f64>),
}

// fn main_multithreaded(
//     io: DynamixelSerialIO,
//     mut master_serial_port: Box<dyn SerialPort>,
//     mut puppet_serial_port: Box<dyn SerialPort>,
// ) -> Result<()> {
//     let (tx, rx) = mpsc::channel();
//     let (tx_dora, rx_dora) = mpsc::channel();
//     let tx_dora_read = tx_dora.clone();
//     std::thread::spawn(move || loop {
//         let now = Instant::now();
//         let pos = xl330::sync_read_present_position(
//             &io,
//             master_serial_port.as_mut(),
//             &SERVOS,
//         )
//         .expect("Read Communication error");
//         tx.send((now, pos.clone())).unwrap();
//         tx_dora_read.send(State::Position(pos)).unwrap();
//     });

//     let io = DynamixelSerialIO::v2();

//     let join = std::thread::spawn(move || {
//         while let Ok((_now, pos)) = rx.recv() {
//             // Compute linear interpolation for gripper as input and output range missmatch
//             // let gripper = (pos[8] - MIN_MASTER_GRIPER) * (MAX_PUPPET_GRIPER - MIN_PUPPET_GRIPER)
//             // / (MAX_MASTER_GRIPER - MIN_MASTER_GRIPER)
//             // + MIN_PUPPET_GRIPER;
//             let target = pos;
//             // target[8] = gripper;
//             xl330::sync_write_goal_position(
//                 &io,
//                 puppet_serial_port.as_mut(),
//                 &SERVOS,
//                 &target,
//             )
//             .expect("Communication error");
//             // println!("elapsed time: {:?}", now.elapsed());
//             tx_dora.send(State::GoalPosition(target)).unwrap();
//         }
//     });

//     if std::env::var("DORA_NODE_CONFIG").is_ok() {
//         let (mut node, mut events) = DoraNode::init_from_env()?;
//         while let Ok(target) = rx_dora.recv() {
//             let parameters = MetadataParameters::default();
//             match target {
//                 State::Position(pos) => {
//                     let output = DataId::from("puppet_goal_position".to_owned());
//                     node.send_output(output.clone(), parameters, pos.into_arrow())?;
//                 }
//                 State::GoalPosition(pos) => {
//                     let output = DataId::from("puppet_state".to_owned());
//                     node.send_output(output.clone(), parameters, pos.into_arrow())?;
//                 }
//             }
//             if events.recv_timeout(Duration::from_nanos(100)).is_none() {
//                 break;
//             }
//         }
//     };
//     join.join().unwrap();
//     Ok(())
// }

fn main_multithreaded(
    io: DynamixelSerialIO,
    mut master_serial_port: Box<dyn SerialPort>,
    mut puppet_serial_port: Box<dyn SerialPort>,
    tx_dora: mpsc::Sender<(Side, State)>,
) -> Result<JoinHandle<()>> {
    let (tx, rx) = mpsc::channel();
    let tx_dora_read = tx_dora.clone();
    std::thread::spawn(move || loop {
        let now = Instant::now();
        let pos = xl330::sync_read_present_position(
            &io,
            master_serial_port.as_mut(),
            &[1, 2, 4, 6, 7, 8, 9], // 3 and 5 are skipped as thery share the same position as 2 and 4
        )
        .expect("Read Communication error");
        let radians: Vec<f64> = pos.iter().map(|&x| xl330::conv::pos_to_radians(x)).collect();
        tx.send((now, radians.clone())).unwrap();
        tx_dora.send((side, State::Position(radians))).unwrap();
        let vel = xl330::sync_read_present_velocity(
            &io,
            master_serial_port.as_mut(),
            &[1, 2, 4, 6, 7, 8, 9], // 3 and 5 are skipped as thery share the same position as 2 and 4
        )
        .expect("Read Communication error");
        let rad_per_sec: Vec<f64> = vel
            .iter()
            .map(|&x| xl330::conv::abs_speed_to_rad_per_sec(x))
            .collect();
        tx_dora.send((side, State::Velocity(rad_per_sec))).unwrap();
        let load =
            xl330::sync_read_present_current(&io, master_serial_port.as_mut(), &[1, 2, 4, 6, 7, 8, 9]) // 3 and 5 are skipped as thery share the same position as 2 and 4
                .expect("Read Communication error");
        tx_dora.send((side, State::Current(load))).unwrap();
    });

    let io = DynamixelSerialIO::v2();
    let join = std::thread::spawn(move || {
        while let Ok((_now, mut pos)) = rx.recv() {
            pos[6] = (pos[6] - MIN_MASTER_GRIPER) * (MAX_PUPPET_GRIPER - MIN_PUPPET_GRIPER)
                / (MAX_MASTER_GRIPER - MIN_MASTER_GRIPER)
                + MIN_PUPPET_GRIPER;
            tx_dora_read
                .send((side, State::GoalPosition(pos.clone())))
                .unwrap();
            pos.insert(2, pos[1]);
            pos.insert(4, pos[3]);
            let pos: Vec<u32> = pos.iter().map(|&x| xl330::conv::radians_to_pos(x)).collect();
            // Compute linear interpolation for gripper as input and output range missmatch
            xl330::sync_write_goal_position(
                &io,
                puppet_serial_port.as_mut(),
                &[1, 2, 3, 4, 5, 6, 7, 8, 9],
                &pos,
            )
            .expect("Write Communication error");
            // println!("elapsed time: {:?}", now.elapsed());
        }
    });

    Ok(join)
}

fn main() -> Result<()> {
    let args = Args::parse();
    let master_path = std::env::var("MASTER_PATH").unwrap_or(args.master_path.clone());
    let puppet_path = std::env::var("PUPPET_PATH").unwrap_or(args.puppet_path.clone());
    let strength = std::env::var("STRENGTH")
        .unwrap_or(args.strength.to_string())
        .parse::<u16>()?;
    let master_baudrate = std::env::var("MASTER_BAUDRATE")
        .unwrap_or(args.master_baudrate.to_string())
        .parse::<u32>()?;
    let puppet_baudrate = std::env::var("PUPPET_BAUDRATE")
        .unwrap_or(args.puppet_baudrate.to_string())
        .parse::<u32>()?;

    let mut master_serial_port = serialport::new(master_path, master_baudrate)
        .timeout(Duration::from_millis(2))
        .open()
        .expect("Failed to open port");
    let mut puppet_serial_port = serialport::new(puppet_path, puppet_baudrate)
        .timeout(Duration::from_millis(2))
        .open()
        .expect("Failed to open port");


    // Prepare puppet
    let io = DynamixelSerialIO::v2();
    xl330::sync_write_torque_enable(&io, puppet_serial_port.as_mut(), &SERVOS, &[1; NUM_SERVOS])
        .expect("Communication error");

    // Prepare master
    let io = DynamixelSerialIO::v2();
    xl330::sync_write_operating_mode(&io, master_serial_port.as_mut(), &[GRIPPER_ID], &[16]).expect("Communication error");

    xl330::sync_write_torque_enable(&io, master_serial_port.as_mut(), &SERVOS, &[0, 0, 0, 0, 0, 1])
        .expect("Communication error");

    xl330::sync_write_goal_pwm(&io, master_serial_port.as_mut(), &[GRIPPER_ID], &[strength]).expect("Communication error");

    let join = main_multithreaded(io, master_serial_port, puppet_serial_port)?;

    Ok(())
}
